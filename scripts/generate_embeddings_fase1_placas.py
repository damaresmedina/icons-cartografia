"""
generate_embeddings_fase1_placas.py
===================================

Fase 1 da Cartografia do Contencioso Constitucional: embedar as 940 placas
(chunks agregados por dispositivo constitucional) usando OpenAI
`text-embedding-3-small` e gravar em `public.embeddings`.

Princípios (ROTAS.md Seção 5):
  - Idempotente: INSERT ON CONFLICT DO NOTHING
  - Log visível: progresso a cada chunk
  - Transação explícita: batch de 100 com commit
  - Recuperação de falha: checkpoint por chunk_slug
  - Sem destruir dado: apenas insere em embeddings

Custo estimado:
  - 940 placas × ~5.000 tokens médios = ~4,7M tokens
  - text-embedding-3-small: US$ 0,02 por 1M tokens
  - Total estimado: ~US$ 0,10

Uso:
    export OPENAI_API_KEY="sk-..."
    python generate_embeddings_fase1_placas.py [--dry-run]

Dry-run: lê os chunks mas não chama a OpenAI. Útil para validar formato.
"""
import os, sys, time, argparse, hashlib
import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────
DSN = "postgresql://postgres:RHuQvsf4shpsPRjP@db.hetuhkhhppxjliiaerlu.supabase.co:6543/postgres"
MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
BATCH_SIZE_OPENAI = 100   # chunks por chamada à API (OpenAI aceita até 2048 inputs)
MAX_TOKENS_PER_INPUT = 8191  # limite do modelo; truncar com tiktoken se preciso
COURT_ID = "stf"

# ─────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true", help="Não chama OpenAI. Valida seleção e formato.")
ap.add_argument("--resume", action="store_true", help="Pula chunks que já têm embedding.")
args = ap.parse_args()

# ─────────────────────────────────────────────────
# Conexão Postgres
# ─────────────────────────────────────────────────
print(f"[{time.strftime('%H:%M:%S')}] Conectando ao Supabase ICONS...")
con = psycopg2.connect(DSN)
con.autocommit = False
cur = con.cursor()

# ─────────────────────────────────────────────────
# Diagnóstico inicial
# ─────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM chunks")
total_chunks = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_model = %s", (MODEL,))
ja_embeddados = cur.fetchone()[0]

print(f"[{time.strftime('%H:%M:%S')}] chunks no banco: {total_chunks}")
print(f"[{time.strftime('%H:%M:%S')}] já embeddados com {MODEL}: {ja_embeddados}")

# ─────────────────────────────────────────────────
# Seleção dos chunks a processar
# ─────────────────────────────────────────────────
query_select = """
SELECT c.chunk_slug, c.chunk_text, c.token_estimate
FROM chunks c
WHERE c.chunk_text IS NOT NULL AND c.chunk_text <> ''
"""
if args.resume:
    query_select += """
      AND NOT EXISTS (
        SELECT 1 FROM embeddings e
        WHERE e.chunk_slug = c.chunk_slug AND e.embedding_model = %s
      )
    """
    cur.execute(query_select, (MODEL,))
else:
    cur.execute(query_select)

chunks_a_processar = cur.fetchall()
print(f"[{time.strftime('%H:%M:%S')}] chunks a processar agora: {len(chunks_a_processar)}")

if not chunks_a_processar:
    print("Nada a fazer. Saindo.")
    cur.close(); con.close(); sys.exit(0)

# ─────────────────────────────────────────────────
# Dry-run
# ─────────────────────────────────────────────────
if args.dry_run:
    total_tokens = sum(int(c[2] or 0) for c in chunks_a_processar)
    custo_estimado = total_tokens / 1_000_000 * 0.02
    print(f"\n── DRY-RUN ──")
    print(f"  Chunks a embedar: {len(chunks_a_processar)}")
    print(f"  Tokens estimados (soma token_estimate): {total_tokens:,}")
    print(f"  Custo estimado text-embedding-3-small: US$ {custo_estimado:.4f}")
    print(f"\n  Amostra das 3 primeiras placas:")
    for slug, texto, toks in chunks_a_processar[:3]:
        print(f"    {slug} — {toks} tokens — texto: {len(texto):,} chars")
    print(f"\nPara executar de verdade: remova --dry-run")
    cur.close(); con.close(); sys.exit(0)

# ─────────────────────────────────────────────────
# Chave OpenAI
# ─────────────────────────────────────────────────
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("ERRO: variável OPENAI_API_KEY não definida.")
    print("   Configure antes de executar:")
    print("       export OPENAI_API_KEY=\"sk-...\"    (bash)")
    print("       $env:OPENAI_API_KEY=\"sk-...\"      (PowerShell)")
    sys.exit(1)

try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
except ImportError:
    print("ERRO: pacote 'openai' não instalado. Rodar: pip install openai")
    sys.exit(1)

# ─────────────────────────────────────────────────
# Loop principal: lotes de BATCH_SIZE_OPENAI
# ─────────────────────────────────────────────────
total = len(chunks_a_processar)
inseridos = 0
erros = 0
tokens_reais = 0
inicio = time.time()

for i in range(0, total, BATCH_SIZE_OPENAI):
    lote = chunks_a_processar[i:i+BATCH_SIZE_OPENAI]
    slugs = [c[0] for c in lote]
    # Truncate agressivo: 8192 tokens * ~3.5 chars/token pt-BR ≈ 28000 chars — usar 24000 para margem
    textos = [(c[1] or '')[:24000] for c in lote]

    try:
        resp = client.embeddings.create(model=MODEL, input=textos)
        vetores = [d.embedding for d in resp.data]
        tokens_reais += resp.usage.total_tokens

        # Prepara linhas para INSERT — vetor convertido para lista-string no formato pgvector
        linhas = []
        for slug, vec in zip(slugs, vetores):
            if len(vec) != DIMENSIONS:
                print(f"  AVISO: {slug} retornou {len(vec)} dims, esperado {DIMENSIONS}")
                continue
            # pgvector aceita literal '[1.0,2.0,...]'
            vec_literal = '[' + ','.join(f'{v:.7f}' for v in vec) + ']'
            linhas.append((slug, MODEL, vec_literal, COURT_ID))

        # INSERT idempotente, um por vez para simplificar (940 chunks é pouco)
        for slug, model_name, vec_literal, court in linhas:
            cur.execute(
                """INSERT INTO embeddings (chunk_slug, embedding_model, vector_ref, court_id, created_at)
                   VALUES (%s, %s, %s::vector, %s, NOW())
                   ON CONFLICT (chunk_slug, embedding_model) DO NOTHING""",
                (slug, model_name, vec_literal, court)
            )
        con.commit()
        inseridos += len(linhas)

        decorrido = time.time() - inicio
        taxa = inseridos / decorrido if decorrido > 0 else 0
        restante = (total - inseridos) / taxa if taxa > 0 else 0
        print(f"[{time.strftime('%H:%M:%S')}] lote {i//BATCH_SIZE_OPENAI + 1}: {len(linhas)} embeddings salvos | "
              f"total: {inseridos}/{total} ({100*inseridos/total:.1f}%) | "
              f"{tokens_reais:,} tokens | eta: {restante:.0f}s")

    except Exception as e:
        erros += 1
        print(f"  ERRO no lote {i//BATCH_SIZE_OPENAI + 1}: {type(e).__name__}: {e}")
        con.rollback()
        if erros >= 3:
            print(f"Muitos erros consecutivos ({erros}). Abortando.")
            break
        time.sleep(2)  # backoff simples

# ─────────────────────────────────────────────────
# Verificação final
# ─────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_model = %s", (MODEL,))
final = cur.fetchone()[0]

duracao = time.time() - inicio
custo_real = tokens_reais / 1_000_000 * 0.02

print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  FIM · {time.strftime('%H:%M:%S')}")
print(f"  Embeddings gravados nesta execução: {inseridos}")
print(f"  Total no banco agora: {final}")
print(f"  Erros: {erros}")
print(f"  Tokens consumidos: {tokens_reais:,}")
print(f"  Custo real OpenAI: US$ {custo_real:.4f}")
print(f"  Duração: {duracao:.1f}s")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

cur.close(); con.close()
