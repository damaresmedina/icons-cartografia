"""
v2.3: Constrói decision_blocks_resolved a partir de decision_blocks_unified.
Lê anchor_slug_final, anchor_quality_final, anchor_confidence_final com fallback.
Inclui anchor_source no output. Cria views analíticas no SQLite.
"""
import sqlite3, json, re, hashlib, os
from collections import Counter
from pathlib import Path

BASE = Path("C:", "/", "projetos", "icons", "ingest", "saida_parser")
DB_PATH = BASE / "cf_comentada_v3.db"

# ══════════════════════════════════════════
# METADADOS
# ══════════════════════════════════════════

CLASSES_PROC = r'ADI|ADC|ADPF|ADO|RE|ARE|HC|RHC|MS|MI|AP|ACO|Rcl|AI|Pet|SS|SL|IF|Inq|Ext|AC|AgR|ED|MC|QO|SV|PSV|AO|AR|RMS|CR|Rp|STA'
RE_PROC = re.compile(rf'\b({CLASSES_PROC})\s*[\-n.\s]*([\d][\d.,]*)', re.IGNORECASE)
RE_REL = re.compile(r'rel\.?\s*(?:p/\s*o?\s*ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_RED = re.compile(r'red\.?\s*(?:do\s+ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_JULG = re.compile(r'j\.\s*(\d[\d\-/]+(?:\s*de\s*\w+\s*de\s*\d+)?)', re.IGNORECASE)
RE_DJE = re.compile(r'D[Jj][Ee]?\s*de\s*(\d[\d\-/]+)', re.IGNORECASE)
RE_TEMA = re.compile(r'[Tt]ema\s*(\d+)')
RE_SV = re.compile(r'S[u\u00fa]mula\s+Vinculante\s*n?[o\u00ba\u00b0]?\s*(\d+)', re.IGNORECASE)
RE_SUMULA = re.compile(r'S[u\u00fa]mula\s*n?[o\u00ba\u00b0]?\s*(\d+)', re.IGNORECASE)

def extract_meta(text):
    meta = {'process_class':'', 'process_number':'', 'relator':'', 'redator':'',
            'julgamento_data':'', 'dje_data':'', 'tema_rg':'', 'sumula_num':''}
    if not text: return meta
    m = RE_PROC.search(text)
    if m:
        meta['process_class'] = m.group(1).upper()
        meta['process_number'] = m.group(2).replace('.','').replace(',','')
    m = RE_REL.search(text)
    if m: meta['relator'] = m.group(1).strip()
    m = RE_RED.search(text)
    if m: meta['redator'] = m.group(1).strip()
    m = RE_JULG.search(text)
    if m: meta['julgamento_data'] = m.group(1).strip()
    m = RE_DJE.search(text)
    if m: meta['dje_data'] = m.group(1).strip()
    m = RE_TEMA.search(text)
    if m: meta['tema_rg'] = m.group(1)
    m = RE_SV.search(text)
    if m: meta['sumula_num'] = m.group(1)
    elif not meta['process_class']:
        m = RE_SUMULA.search(text)
        if m: meta['sumula_num'] = m.group(1)
    return meta

def build_process_key(cls, num):
    if not cls and not num: return None
    cls = (cls or '').upper().strip()
    num = (num or '').strip().rstrip('.')
    if cls and num:
        return f"{cls}_{num}"
    return num or cls

def classify_unit_type(editorial, metadata, process_class, tema):
    ed = (editorial or '').lower()
    if tema:
        return 'repercussao_geral'
    if 'sumula_vinculante' in ed or 'S\u00famula Vinculante' in (metadata or ''):
        return 'sumula_vinculante'
    if 'sumula' in ed:
        return 'sumula'
    if 'controle_concentrado' in ed:
        if process_class in ('ADI','ADC','ADPF','ADO'):
            return 'controle_concentrado'
        return 'controle_concentrado'
    if 'repercussao_geral' in ed:
        return 'repercussao_geral'
    if 'julgados_correlatos' in ed or 'julgado_correlato' in ed:
        return 'julgado_correlato'
    if process_class:
        return 'julgado_principal'
    return 'comentario_editorial'

def block_hash(anchor_slug, editorial, block_text, metadata):
    raw = f"{anchor_slug}|{editorial}|{(block_text or '')[:200]}|{(metadata or '')[:100]}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]

# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

print(f"Lendo banco: {DB_PATH}")
con = sqlite3.connect(str(DB_PATH))
con.row_factory = sqlite3.Row

rows = con.execute("SELECT * FROM decision_blocks_unified").fetchall()
print(f"Blocos lidos: {len(rows)}")

# Drop and recreate
con.execute("DROP TABLE IF EXISTS decision_blocks_resolved")
con.execute("""
CREATE TABLE decision_blocks_resolved (
    block_id             INTEGER PRIMARY KEY,
    paragraph_start      INTEGER,
    paragraph_end        INTEGER,

    anchor_slug          TEXT,
    anchor_label         TEXT,
    anchor_node_type     TEXT,
    anchor_quality       TEXT,
    anchor_confidence    REAL,
    anchor_source        TEXT,

    matched_variant      TEXT,
    variant_origin       TEXT,
    match_priority       INTEGER,
    context_relation     TEXT,
    namespace            TEXT,

    editorial_marker     TEXT,
    editorial_label      TEXT,
    decision_unit_type   TEXT,

    block_text           TEXT,
    metadata_text        TEXT,

    process_class        TEXT,
    process_number       TEXT,
    process_key          TEXT,
    relator              TEXT,
    redator              TEXT,
    julgamento_data      TEXT,
    dje_data             TEXT,
    tema_rg              TEXT,
    sumula_num           TEXT,

    raw_signature        TEXT,
    block_hash           TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Process each block
resolved = []
for r in rows:
    d = dict(r)
    meta_text = d.get('metadata_text', '') or ''
    block_text = d.get('block_text', '') or ''
    combined = block_text + '\n' + meta_text

    meta = extract_meta(meta_text)
    if not meta['relator']:
        meta.update(extract_meta(block_text[:200]))

    ed = d.get('editorial_marker', '') or ''
    pc = meta['process_class'] or d.get('process_class', '')
    pn = meta['process_number'] or d.get('process_number', '')
    rel = meta['relator'] or d.get('relator', '')
    tema = meta['tema_rg'] or d.get('tema', '')

    anchor_slug = d.get('anchor_slug_final', '') or d.get('anchor_slug', '')

    pk = build_process_key(pc, pn)
    dut = classify_unit_type(ed, meta_text, pc, tema)
    bh = block_hash(anchor_slug, ed, block_text, meta_text)
    quality = d.get('anchor_quality_final', '') or d.get('anchor_quality', '')
    confidence = d.get('anchor_confidence_final', '') or d.get('anchor_confidence')
    anchor_source = d.get('anchor_source', '')
    if confidence:
        try: confidence = float(confidence)
        except: confidence = None

    ns = 'adct' if anchor_slug == 'adct' else 'cf'

    resolved.append({
        'block_id': d.get('block_id'),
        'paragraph_start': d.get('paragraph_start'),
        'paragraph_end': d.get('paragraph_end'),
        'anchor_slug': anchor_slug,
        'anchor_label': d.get('node_label', ''),
        'anchor_node_type': d.get('node_type', ''),
        'anchor_quality': quality,
        'anchor_confidence': confidence,
        'anchor_source': anchor_source,
        'matched_variant': d.get('matched_variant', ''),
        'variant_origin': d.get('variant_origin', ''),
        'match_priority': d.get('match_priority'),
        'context_relation': ed,
        'namespace': ns,
        'editorial_marker': ed,
        'editorial_label': ed.replace('_', ' ').title() if ed else '',
        'decision_unit_type': dut,
        'block_text': block_text,
        'metadata_text': meta_text,
        'process_class': pc,
        'process_number': pn,
        'process_key': pk,
        'relator': rel,
        'redator': meta['redator'],
        'julgamento_data': meta['julgamento_data'] or d.get('data_julgamento', ''),
        'dje_data': meta['dje_data'] or d.get('dje', ''),
        'tema_rg': tema,
        'sumula_num': meta['sumula_num'],
        'raw_signature': f"{pc} {pn} rel. {rel}".strip(),
        'block_hash': bh,
    })

# Insert
cols = list(resolved[0].keys())
placeholders = ','.join('?' for _ in cols)
con.executemany(
    f"INSERT INTO decision_blocks_resolved ({",".join(cols)}) VALUES ({placeholders})",
    [[r[c] for c in cols] for r in resolved]
)

# Indexes
con.execute("CREATE INDEX IF NOT EXISTS idx_dbr_slug ON decision_blocks_resolved(anchor_slug)")
con.execute("CREATE INDEX IF NOT EXISTS idx_dbr_quality ON decision_blocks_resolved(anchor_quality)")
con.execute("CREATE INDEX IF NOT EXISTS idx_dbr_relator ON decision_blocks_resolved(relator)")
con.execute("CREATE INDEX IF NOT EXISTS idx_dbr_pkey ON decision_blocks_resolved(process_key)")
con.execute("CREATE INDEX IF NOT EXISTS idx_dbr_dut ON decision_blocks_resolved(decision_unit_type)")
con.execute("CREATE INDEX IF NOT EXISTS idx_dbr_class ON decision_blocks_resolved(process_class)")
con.execute("CREATE INDEX IF NOT EXISTS idx_dbr_ns ON decision_blocks_resolved(namespace)")
con.execute("CREATE INDEX IF NOT EXISTS idx_dbr_source ON decision_blocks_resolved(anchor_source)")

# Views
con.execute("DROP VIEW IF EXISTS v_relator_anchor_distribution")
con.execute("""
CREATE VIEW v_relator_anchor_distribution AS
SELECT relator, anchor_slug, decision_unit_type, COUNT(*) as n
FROM decision_blocks_resolved
WHERE relator IS NOT NULL AND relator != ''
GROUP BY relator, anchor_slug, decision_unit_type
""")

con.execute("DROP VIEW IF EXISTS v_anchor_decision_distribution")
con.execute("""
CREATE VIEW v_anchor_decision_distribution AS
SELECT anchor_slug, decision_unit_type, COUNT(*) as n
FROM decision_blocks_resolved
WHERE anchor_slug IS NOT NULL AND anchor_slug != ''
GROUP BY anchor_slug, decision_unit_type
""")

con.execute("DROP VIEW IF EXISTS v_process_occurrence_network")
con.execute("""
CREATE VIEW v_process_occurrence_network AS
SELECT process_key, anchor_slug, editorial_marker, COUNT(*) as n
FROM decision_blocks_resolved
WHERE process_key IS NOT NULL AND process_key != ''
GROUP BY process_key, anchor_slug, editorial_marker
""")

con.execute("DROP VIEW IF EXISTS v_relator_process_network")
con.execute("""
CREATE VIEW v_relator_process_network AS
SELECT relator, process_key, anchor_slug, COUNT(*) as n
FROM decision_blocks_resolved
WHERE relator IS NOT NULL AND relator != '' AND process_key IS NOT NULL
GROUP BY relator, process_key, anchor_slug
""")

con.commit()

# ══════════════════════════════════════════
# DIAGNOSTICO
# ══════════════════════════════════════════

total = len(resolved)
print(f"\n{'='*70}")
print(f"  DECISION BLOCKS RESOLVED")
print(f"{'='*70}")
print(f"  Total: {total}")

dut_counts = Counter(r['decision_unit_type'] for r in resolved)
print(f"\n  Por decision_unit_type:")
for t, n in dut_counts.most_common():
    print(f"    {t:30s} {n:5d} ({n/total*100:.1f}%)")

qual_counts = Counter(r['anchor_quality'] for r in resolved)
print(f"\n  Por anchor_quality:")
for q, n in qual_counts.most_common():
    print(f"    {q:15s} {n:5d}")

src_counts = Counter(r['anchor_source'] for r in resolved)
print(f"\n  Por anchor_source:")
for s, n in src_counts.most_common():
    print(f"    {s or '(vazio)':15s} {n:5d}")

with_pk = sum(1 for r in resolved if r['process_key'])
with_rel = sum(1 for r in resolved if r['relator'])
with_tema = sum(1 for r in resolved if r['tema_rg'])
with_sv = sum(1 for r in resolved if r['sumula_num'])
print(f"\n  Com process_key: {with_pk}")
print(f"  Com relator: {with_rel}")
print(f"  Com tema_rg: {with_tema}")
print(f"  Com sumula_num: {with_sv}")

# Process keys unicos
pks = set(r['process_key'] for r in resolved if r['process_key'])
print(f"  Process keys unicos: {len(pks)}")
rels = set(r['relator'] for r in resolved if r['relator'])
print(f"  Relatores unicos: {len(rels)}")

# Top relatores
rel_counts = Counter(r['relator'] for r in resolved if r['relator'])
print(f"\n  Top 10 relatores:")
for r, n in rel_counts.most_common(10):
    print(f"    {r:30s} {n:5d}")

# Top process classes
cls_counts = Counter(r['process_class'] for r in resolved if r['process_class'])
print(f"\n  Top 10 classes:")
for c, n in cls_counts.most_common(10):
    print(f"    {c:10s} {n:5d}")

# Views test
print(f"\n  Views criadas:")
for vname in ['v_relator_anchor_distribution', 'v_anchor_decision_distribution', 'v_process_occurrence_network', 'v_relator_process_network']:
    cnt = con.execute(f"SELECT COUNT(*) FROM {vname}").fetchone()[0]
    print(f"    {vname}: {cnt} linhas")

# Sample
print(f"\n  Amostra Art. 5:")
for r in con.execute("SELECT process_key, relator, decision_unit_type, anchor_quality, anchor_source, substr(block_text,1,50) FROM decision_blocks_resolved WHERE anchor_slug LIKE 'cf-1988-art-5%' LIMIT 5").fetchall():
    print(f"    {r[0] or '':20s} | {r[1] or '':15s} | {r[2]:25s} | {r[3]:10s} | {r[4] or '':10s} | {r[5]}")

con.close()
print(f"\n  DB: {DB_PATH} ({os.path.getsize(str(DB_PATH))/1024/1024:.1f} MB)")
print(f"  Pronto.")
