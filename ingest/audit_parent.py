import sqlite3, os, re
from collections import Counter

DB = os.path.join("C:", os.sep, "projetos", "icons", "ingest", "saida_parser", "cf_comentada_v2.db")
con = sqlite3.connect(DB)

print("=" * 70)
print("  AUDITORIA DE MATCH PARENT")
print("=" * 70)

total = con.execute("SELECT COUNT(*) FROM commentary_blocks WHERE match_type = 'parent'").fetchone()[0]
print(f"\nTotal parent: {total}")

# Analyze lost level
rows = con.execute("""
    SELECT anchor_slug_norm, anchor_slug
    FROM commentary_blocks WHERE match_type = 'parent'
""").fetchall()

lost_level = Counter()
for norm, matched in rows:
    norm = norm or ''
    matched = matched or ''
    has_ali = '-ali-' in norm
    has_inc = '-inc-' in norm
    has_par = '-par-' in norm
    m_ali = '-ali-' in matched
    m_inc = '-inc-' in matched
    m_par = '-par-' in matched

    if has_ali and not m_ali:
        lost_level['alinea->pai'] += 1
    elif has_inc and not m_inc:
        lost_level['inciso->art'] += 1
    elif has_par and not m_par:
        lost_level['paragrafo->art'] += 1
    else:
        lost_level['outro'] += 1

print(f"\nNivel perdido:")
for level, cnt in lost_level.most_common():
    print(f"  {level:25s}: {cnt:5d} ({cnt/total*100:.1f}%)")

# Samples
print(f"\n--- INCISO->ART (amostra 10) ---")
for r in con.execute("""
    SELECT block_id, anchor_slug_norm, anchor_slug, anchor_artigo, process_full, substr(block_text,1,100)
    FROM commentary_blocks WHERE match_type='parent' AND anchor_slug_norm LIKE '%inc%' AND anchor_slug NOT LIKE '%inc%'
    ORDER BY RANDOM() LIMIT 10
""").fetchall():
    print(f"  [{r[0]}] {r[1]} -> {r[2]} | {r[4] or ''}")
    print(f"    {r[5]}")

print(f"\n--- PARAGRAFO->ART (amostra 10) ---")
for r in con.execute("""
    SELECT block_id, anchor_slug_norm, anchor_slug, anchor_artigo, process_full, substr(block_text,1,100)
    FROM commentary_blocks WHERE match_type='parent' AND anchor_slug_norm LIKE '%par%' AND anchor_slug NOT LIKE '%par%'
    ORDER BY RANDOM() LIMIT 10
""").fetchall():
    print(f"  [{r[0]}] {r[1]} -> {r[2]} | {r[4] or ''}")
    print(f"    {r[5]}")

# Top artigos com parent
print(f"\n--- TOP 15 ARTIGOS COM PARENT ---")
for r in con.execute("""
    SELECT anchor_artigo, COUNT(*) as n FROM commentary_blocks
    WHERE match_type='parent' AND anchor_artigo IS NOT NULL
    GROUP BY anchor_artigo ORDER BY n DESC LIMIT 15
""").fetchall():
    print(f"  Art. {r[0]:>5s}: {r[1]:5d}")

# ══════════════════════════════════════════
# PARTE 2: Criar colunas de qualidade
# ══════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  CRIANDO COLUNAS DE QUALIDADE")
print(f"{'='*70}")

try:
    con.execute("ALTER TABLE commentary_blocks ADD COLUMN anchor_quality TEXT")
except: pass
try:
    con.execute("ALTER TABLE commentary_blocks ADD COLUMN anchor_confidence REAL")
except: pass

con.execute("UPDATE commentary_blocks SET anchor_quality='exact', anchor_confidence=1.0 WHERE match_type='exact'")

con.execute("""
    UPDATE commentary_blocks SET
        anchor_quality = 'parent',
        anchor_confidence = CASE
            WHEN anchor_slug_norm LIKE '%ali%' AND anchor_slug NOT LIKE '%ali%' THEN 0.5
            WHEN anchor_slug_norm LIKE '%inc%' AND anchor_slug NOT LIKE '%inc%' THEN 0.6
            WHEN anchor_slug_norm LIKE '%par%' AND anchor_slug NOT LIKE '%par%' THEN 0.7
            ELSE 0.8
        END
    WHERE match_type = 'parent'
""")

con.execute("UPDATE commentary_blocks SET anchor_quality='adct', anchor_confidence=0.3 WHERE match_type='adct'")
con.execute("UPDATE commentary_blocks SET anchor_quality='unresolved', anchor_confidence=0.0 WHERE match_type='none' OR match_type IS NULL")

con.execute("CREATE INDEX IF NOT EXISTS idx_cb_quality ON commentary_blocks(anchor_quality)")
con.execute("CREATE INDEX IF NOT EXISTS idx_cb_confidence ON commentary_blocks(anchor_confidence)")
con.commit()

print(f"\n  Distribuicao:")
for r in con.execute("SELECT anchor_quality, COUNT(*), ROUND(AVG(anchor_confidence),2) FROM commentary_blocks GROUP BY anchor_quality ORDER BY AVG(anchor_confidence) DESC").fetchall():
    print(f"    {r[0] or 'NULL':15s} {r[1]:5d} blocos  (conf media: {r[2]})")

print(f"\n  Confidence media global: {con.execute('SELECT ROUND(AVG(anchor_confidence),3) FROM commentary_blocks').fetchone()[0]}")

con.close()
print(f"\nPronto.")
