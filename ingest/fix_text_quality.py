"""
Correção geral de texto:
1. Normaliza nomes de relatores (truncados, duplicados, lixo)
2. Recupera block_text de blocos vazios do HTML do STF
3. Remove artefatos de texto
"""
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")
HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")

con = sqlite3.connect(str(DB_PATH))
stf_html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

# ═══════════════════════════════════════════
# 1. NORMALIZAR RELATORES
# ═══════════════════════════════════════════

print("1. Normalizando relatores...")

RELATOR_MAP = {
    # Truncados -> nome completo
    'Al': '',
    'O': '',
    'Sep': 'Sepúlveda Pertence',
    'Ceza': 'Cezar Peluso',
    'Cezar Pel': 'Cezar Peluso',
    'Cezar Pelus': 'Cezar Peluso',
    'Dias': 'Dias Toffoli',
    'Eros Gr': 'Eros Grau',
    'Marco': 'Marco Aurélio',
    'Marco A': 'Marco Aurélio',
    'Marco Aur': 'Marco Aurélio',
    'Marco Aurélio': 'Marco Aurélio',  # fix encoding
    'Nelson': 'Nelson Jobim',
    'Nelson Job': 'Nelson Jobim',
    'Ricardo Le': 'Ricardo Lewandowski',
    'Luís Rober': 'Luís Roberto Barroso',

    # Duplicados -> forma canônica
    'Marco Aurelio': 'Marco Aurélio',
    'Carmen Lúcia': 'Cármen Lúcia',
    'Carmén Lúcia': 'Cármen Lúcia',
    'Alexandre Moraes': 'Alexandre de Moraes',
    'Dias Tofolli': 'Dias Toffoli',
    'Sidney Sanches': 'Sydney Sanches',
    'Rosa Werber': 'Rosa Weber',
    'Carlos Britto': 'Ayres Britto',

    # Com lixo
    'Ayres Britto)': 'Ayres Britto',
    'Luís Roberto Barroso-': 'Luís Roberto Barroso',

    # Roberto Barroso -> Luís Roberto Barroso (unificar)
    'Roberto Barroso': 'Luís Roberto Barroso',
}

# Also fix any relator containing extra text after the name
RE_RELATOR_JUNK = re.compile(r'^([A-ZÀ-Ú][a-záéíóúàâêôãõçü]+(?:\s+(?:de\s+)?[A-ZÀ-Ú][a-záéíóúàâêôãõçü]+){0,3}).*$')

fixed_rel = 0
for old, new in RELATOR_MAP.items():
    n = con.execute(
        "UPDATE decision_blocks_resolved SET relator = ? WHERE relator = ?",
        (new, old)
    ).rowcount
    if n:
        print(f"  '{old}' -> '{new}': {n}")
        fixed_rel += n

# Fix relators with junk after name (like "Ilmar Galvão) proposta pela...")
junk_rels = con.execute(
    "SELECT DISTINCT relator FROM decision_blocks_resolved WHERE relator LIKE '%(%' OR relator LIKE '%;%' OR LENGTH(relator) > 30"
).fetchall()
for (rel,) in junk_rels:
    m = RE_RELATOR_JUNK.match(rel)
    if m:
        clean = m.group(1).strip()
        if clean != rel:
            n = con.execute("UPDATE decision_blocks_resolved SET relator = ? WHERE relator = ?", (clean, rel)).rowcount
            print(f"  '{rel[:40]}...' -> '{clean}': {n}")
            fixed_rel += n

# Also update raw_signature
con.execute("""
    UPDATE decision_blocks_resolved
    SET raw_signature = TRIM(process_class || ' ' || process_number || ' rel. ' || relator)
    WHERE relator != ''
""")

print(f"  Total relator fixes: {fixed_rel}")

# ═══════════════════════════════════════════
# 2. RECUPERAR BLOCOS VAZIOS DO HTML DO STF
# ═══════════════════════════════════════════

print("\n2. Recuperando blocos vazios do HTML...")

def strip_html(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'&ordm;', 'º', s)
    s = re.sub(r'&ldquo;', '"', s)
    s = re.sub(r'&rdquo;', '"', s)
    s = re.sub(r'&lsquo;', "'", s)
    s = re.sub(r'&rsquo;', "'", s)
    s = re.sub(r'&ndash;', '–', s)
    s = re.sub(r'&mdash;', '—', s)
    s = re.sub(r'&sect;', '§', s)
    s = re.sub(r'&amp;', '&', s)
    s = re.sub(r'&[a-z]+;', '', s)
    s = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

EDITORIAL_PREFIXES = [
    'Controle concentrado de constitucionalidade',
    'Controle de concentrado de constitucionalidade',
    'Repercussão geral', 'Repercussão Geral',
    'Súmula Vinculante', 'Súmula vinculante',
    'Julgados correlatos', 'Julgado correlato',
    'Julgados Correlatos', 'Julgado Correlato',
    'Súmula', 'Preâmbulo',
]

# Build com_id -> full text from HTML
com_texts = {}
for m in re.finditer(r'<div\s+class="com"\s+id="com(\d+)"[^>]*>(.*?)</div>', stf_html, re.DOTALL):
    com_id = int(m.group(1))
    raw = strip_html(m.group(2))
    # Strip editorial prefix
    for pfx in EDITORIAL_PREFIXES:
        if raw.startswith(pfx):
            raw = raw[len(pfx):].strip()
            break
    # Split text / metadata
    meta_m = re.search(r'\[([^\]]{10,})\]\s*$', raw)
    if meta_m:
        text = raw[:meta_m.start()].strip()
        meta = meta_m.group(1).strip()
    else:
        text = raw
        meta = ''
    com_texts[com_id] = (text, meta)

print(f"  STF com blocks parsed: {len(com_texts)}")

# Fix empty blocks that have stf_com_id
empty_stf = con.execute("""
    SELECT block_id, stf_com_id FROM decision_blocks_resolved
    WHERE (block_text IS NULL OR block_text = '')
    AND stf_com_id IS NOT NULL
""").fetchall()

recovered = 0
for bid, com_id in empty_stf:
    if com_id in com_texts:
        text, meta = com_texts[com_id]
        if text:
            con.execute("""
                UPDATE decision_blocks_resolved
                SET block_text = ?, metadata_text = COALESCE(NULLIF(metadata_text, ''), ?)
                WHERE block_id = ?
            """, (text, meta, bid))
            recovered += 1

print(f"  Blocos recuperados: {recovered}")

# ═══════════════════════════════════════════
# 3. LIMPAR ARTEFATOS DE TEXTO
# ═══════════════════════════════════════════

print("\n3. Limpando artefatos de texto...")

# Trim block_text and metadata_text
con.execute("UPDATE decision_blocks_resolved SET block_text = TRIM(block_text) WHERE block_text != TRIM(block_text)")
con.execute("UPDATE decision_blocks_resolved SET metadata_text = TRIM(metadata_text) WHERE metadata_text != TRIM(metadata_text)")

# Fix editorial markers that leaked into block_text start
for pfx in EDITORIAL_PREFIXES:
    n = con.execute("""
        UPDATE decision_blocks_resolved
        SET block_text = TRIM(SUBSTR(block_text, ?))
        WHERE block_text LIKE ? || '%'
    """, (len(pfx) + 1, pfx)).rowcount
    if n:
        print(f"  Stripped '{pfx}' from {n} blocks")

# ═══════════════════════════════════════════
# 4. RE-EXTRACT METADATA FOR RECOVERED BLOCKS
# ═══════════════════════════════════════════

print("\n4. Re-extracting metadata for recovered blocks...")

RE_PROC = re.compile(r'\b(ADI|ADC|ADPF|ADO|RE|ARE|HC|RHC|MS|MI|AP|ACO|Rcl|AI|Pet|SS|SL|IF|Inq|Ext|AC|AgR|ED|MC|QO|SV|PSV|AO|AR|RMS|CR|Rp|STA)\s*[\-n.\s]*([\d][\d.,]*)', re.IGNORECASE)
RE_REL = re.compile(r'rel\.?\s*(?:p/\s*o?\s*ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_TEMA = re.compile(r'[Tt]ema\s*(\d+)')

# Blocks that now have text but still missing process_class/relator
needs_meta = con.execute("""
    SELECT block_id, block_text, metadata_text FROM decision_blocks_resolved
    WHERE block_text != '' AND (process_class IS NULL OR process_class = '')
    AND anchor_source = 'stf_import'
""").fetchall()

meta_fixed = 0
for bid, text, meta in needs_meta:
    source = (meta or '') + ' ' + (text or '')[:200]
    m = RE_PROC.search(source)
    pc = m.group(1).upper() if m else ''
    pn = m.group(2).replace('.', '').replace(',', '') if m else ''
    pk = f"{pc}_{pn}" if pc and pn else None

    m = RE_REL.search(source)
    rel = m.group(1).strip() if m else ''
    # Clean relator
    if rel and len(rel) > 30:
        rm = re.match(r'^([A-ZÀ-Ú][a-záéíóúàâêôãõçü]+(?:\s+(?:de\s+)?[A-ZÀ-Ú][a-záéíóúàâêôãõçü]+){0,3})', rel)
        rel = rm.group(1).strip() if rm else ''

    m = RE_TEMA.search(source)
    tema = m.group(1) if m else ''

    if pc or rel:
        con.execute("""
            UPDATE decision_blocks_resolved
            SET process_class = ?, process_number = ?, process_key = ?,
                relator = COALESCE(NULLIF(relator, ''), ?),
                tema_rg = COALESCE(NULLIF(tema_rg, ''), ?),
                raw_signature = TRIM(? || ' ' || ? || ' rel. ' || ?)
            WHERE block_id = ?
        """, (pc, pn, pk, rel, tema, pc, pn, rel, bid))
        meta_fixed += 1

print(f"  Metadata re-extracted: {meta_fixed}")

con.commit()

# ═══════════════════════════════════════════
# 5. VERIFICATION
# ═══════════════════════════════════════════

print(f"\n{'='*60}")
print(f"  RESULTADO")
print(f"{'='*60}")

total = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved").fetchone()[0]
empty = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE (block_text IS NULL OR block_text = '') AND anchor_source = 'stf_import'").fetchone()[0]
norm = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE decision_unit_type = 'dispositivo_normativo'").fetchone()[0]
with_rel = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE relator IS NOT NULL AND relator != ''").fetchone()[0]
with_pc = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE process_class IS NOT NULL AND process_class != ''").fetchone()[0]

print(f"  Total blocos: {total}")
print(f"  STF vazios restantes: {empty}")
print(f"  Normativos (sem decisão): {norm}")
print(f"  Com relator: {with_rel}")
print(f"  Com process_class: {with_pc}")

print(f"\n  Relatores únicos:")
for r in con.execute("SELECT relator, COUNT(*) as n FROM decision_blocks_resolved WHERE relator != '' GROUP BY relator ORDER BY n DESC LIMIT 25").fetchall():
    print(f"    {r[1]:4d} | {r[0]}")

con.close()
print("\nDone.")
