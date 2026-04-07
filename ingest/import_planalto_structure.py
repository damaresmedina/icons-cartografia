"""
Importa a estrutura normativa completa da CF do Planalto (250 arts CF + 138 ADCT)
e acopla as decisões do STF já importadas.
Artigos sem decisão ficam como nó normativo com block_text vazio.
"""
import re
import sqlite3
import hashlib
from collections import defaultdict
from pathlib import Path

PLANALTO_PATH = Path(r"C:\projetos\icons\ingest\cf_planalto.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")

with open(PLANALTO_PATH, 'rb') as f:
    html = f.read().decode('latin-1')

# ═══════════════════════════════════════════
# 1. PARSE PLANALTO: extrair texto normativo de cada artigo
# ═══════════════════════════════════════════

print("Parsing Planalto...")

def strip_html(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'&[a-z]+;', ' ', s)
    s = re.sub(r'&#\d+;', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# Find ADCT boundary (ATO DAS DISPOSIÇÕES in caps)
adct_pos = html.find('ATO DAS DISPOSI')
print(f"  ADCT boundary: {adct_pos}")

# Find all article positions with their text
art_pattern = re.compile(r'Art\.\s*(\d+)[^\n<]{0,500}', re.DOTALL)

cf_articles = {}   # num -> label text
adct_articles = {}  # num -> label text

for m in art_pattern.finditer(html):
    num = int(m.group(1))
    pos = m.start()

    # Get surrounding text for label (up to next Art. or 500 chars)
    end = min(pos + 1000, len(html))
    next_art = art_pattern.search(html, pos + 10)
    if next_art:
        end = min(end, next_art.start())

    chunk = html[pos:end]
    label = strip_html(chunk)[:200]

    if pos < adct_pos:
        if num not in cf_articles:  # keep first occurrence
            cf_articles[num] = label
    else:
        if num not in adct_articles:
            adct_articles[num] = label

print(f"  CF articles: {len(cf_articles)} (1-{max(cf_articles)})")
print(f"  ADCT articles: {len(adct_articles)} (1-{max(adct_articles)})")

# ═══════════════════════════════════════════
# 2. LOAD EXISTING STF DECISIONS FROM DB
# ═══════════════════════════════════════════

print("\nLoading existing STF decisions...")
con = sqlite3.connect(str(DB_PATH))

# Get all existing blocks
existing = con.execute("""
    SELECT block_id, anchor_slug, anchor_label, anchor_node_type,
           anchor_quality, anchor_confidence, anchor_source,
           matched_variant, variant_origin, match_priority,
           context_relation, namespace, editorial_marker, editorial_label,
           decision_unit_type, block_text, metadata_text,
           process_class, process_number, process_key,
           relator, redator, julgamento_data, dje_data,
           tema_rg, sumula_num, raw_signature, block_hash,
           anchor_quality_recode, anchor_resolution_status,
           decision_explicitness, stf_com_id
    FROM decision_blocks_resolved
    ORDER BY block_id
""").fetchall()

col_names = [
    'block_id', 'anchor_slug', 'anchor_label', 'anchor_node_type',
    'anchor_quality', 'anchor_confidence', 'anchor_source',
    'matched_variant', 'variant_origin', 'match_priority',
    'context_relation', 'namespace', 'editorial_marker', 'editorial_label',
    'decision_unit_type', 'block_text', 'metadata_text',
    'process_class', 'process_number', 'process_key',
    'relator', 'redator', 'julgamento_data', 'dje_data',
    'tema_rg', 'sumula_num', 'raw_signature', 'block_hash',
    'anchor_quality_recode', 'anchor_resolution_status',
    'decision_explicitness', 'stf_com_id'
]

# Group by article number
stf_by_cf = defaultdict(list)
stf_by_adct = defaultdict(list)

for row in existing:
    d = dict(zip(col_names, row))
    slug = d['anchor_slug']
    m_cf = re.match(r'cf-1988-art-(\d+)', slug)
    m_adct = re.match(r'adct-art-(\d+)', slug)
    if m_cf:
        stf_by_cf[int(m_cf.group(1))].append(d)
    elif m_adct:
        stf_by_adct[int(m_adct.group(1))].append(d)

print(f"  STF decisions: {len(existing)}")
print(f"  CF articles with decisions: {len(stf_by_cf)}")
print(f"  ADCT articles with decisions: {len(stf_by_adct)}")

# ═══════════════════════════════════════════
# 3. REBUILD: all 388 articles + STF decisions
# ═══════════════════════════════════════════

print("\nRebuilding complete table...")

# Drop views and old table
for vname in con.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall():
    con.execute(f"DROP VIEW IF EXISTS [{vname[0]}]")

con.execute("DROP TABLE IF EXISTS decision_blocks_resolved_backup")
con.execute("ALTER TABLE decision_blocks_resolved RENAME TO decision_blocks_resolved_backup")

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
    anchor_quality_recode TEXT,
    anchor_resolution_status TEXT,
    decision_explicitness TEXT,
    stf_com_id           INTEGER,
    normative_text       TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

block_id = 1
cf_with_decisions = 0
cf_empty = 0
adct_with_decisions = 0
adct_empty = 0

insert_cols = [
    'block_id', 'paragraph_start', 'paragraph_end', 'anchor_slug',
    'anchor_label', 'anchor_node_type', 'anchor_quality', 'anchor_confidence',
    'anchor_source', 'matched_variant', 'variant_origin', 'match_priority',
    'context_relation', 'namespace', 'editorial_marker', 'editorial_label',
    'decision_unit_type', 'block_text', 'metadata_text',
    'process_class', 'process_number', 'process_key',
    'relator', 'redator', 'julgamento_data', 'dje_data',
    'tema_rg', 'sumula_num', 'raw_signature', 'block_hash',
    'anchor_quality_recode', 'anchor_resolution_status',
    'decision_explicitness', 'stf_com_id', 'normative_text'
]
placeholders = ','.join('?' for _ in insert_cols)
insert_sql = f"INSERT INTO decision_blocks_resolved ({','.join(insert_cols)}) VALUES ({placeholders})"

# CF articles (1-250)
for art_num in range(1, 251):
    slug = f"cf-1988-art-{art_num}"
    label = cf_articles.get(art_num, f"Art. {art_num}")
    normative = label
    decisions = stf_by_cf.get(art_num, [])

    if decisions:
        cf_with_decisions += 1
        for d in decisions:
            d['block_id'] = block_id
            d['normative_text'] = normative
            values = [d.get(c, None) for c in insert_cols]
            values[0] = block_id  # block_id
            con.execute(insert_sql, values)
            block_id += 1
    else:
        # Article exists but no decisions — insert normative placeholder
        cf_empty += 1
        bh = hashlib.md5(f"{slug}|normativo|{normative[:100]}".encode()).hexdigest()[:16]
        values = [
            block_id, None, None, slug,
            f"Art. {art_num}", 'artigo', 'normativo', 1.0,
            'planalto', '', '', None,
            '', 'cf', '', '',
            'dispositivo_normativo', '', '',
            '', '', None,
            '', '', '', '',
            '', '', '', bh,
            'normativo', 'resolved', '',
            None, normative
        ]
        con.execute(insert_sql, values)
        block_id += 1

# ADCT articles (1-138)
for art_num in range(1, 139):
    slug = f"adct-art-{art_num}"
    label = adct_articles.get(art_num, f"Art. {art_num} (ADCT)")
    normative = label
    decisions = stf_by_adct.get(art_num, [])

    if decisions:
        adct_with_decisions += 1
        for d in decisions:
            d['block_id'] = block_id
            d['normative_text'] = normative
            values = [d.get(c, None) for c in insert_cols]
            values[0] = block_id
            con.execute(insert_sql, values)
            block_id += 1
    else:
        adct_empty += 1
        bh = hashlib.md5(f"{slug}|normativo|{normative[:100]}".encode()).hexdigest()[:16]
        values = [
            block_id, None, None, slug,
            f"Art. {art_num} (ADCT)", 'artigo', 'normativo', 1.0,
            'planalto', '', '', None,
            '', 'adct', '', '',
            'dispositivo_normativo', '', '',
            '', '', None,
            '', '', '', '',
            '', '', '', bh,
            'normativo', 'resolved', '',
            None, normative
        ]
        con.execute(insert_sql, values)
        block_id += 1

# Indexes
for col in ['anchor_slug', 'anchor_quality', 'relator', 'process_key',
            'decision_unit_type', 'process_class', 'namespace', 'anchor_source',
            'anchor_quality_recode', 'anchor_resolution_status', 'decision_explicitness',
            'editorial_marker', 'stf_com_id']:
    con.execute(f"CREATE INDEX IF NOT EXISTS idx_dbr_{col} ON decision_blocks_resolved({col})")

# Rebuild block_anchors
con.execute("DROP TABLE IF EXISTS block_anchors")
con.execute("""
CREATE TABLE block_anchors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id INTEGER NOT NULL,
    anchor_slug TEXT NOT NULL,
    anchor_role TEXT DEFAULT 'primary',
    confidence REAL,
    source TEXT
)
""")
con.execute("""
    INSERT INTO block_anchors (block_id, anchor_slug, anchor_role, confidence, source)
    SELECT block_id, anchor_slug, 'primary', anchor_confidence, anchor_source
    FROM decision_blocks_resolved
    WHERE anchor_slug IS NOT NULL AND anchor_slug != ''
""")
con.execute("CREATE INDEX idx_ba_block ON block_anchors(block_id)")
con.execute("CREATE INDEX idx_ba_slug ON block_anchors(anchor_slug)")

# Materialized views
for tname in ['v_anchor_quality_recode_distribution', 'v_anchor_resolution_status_distribution',
              'v_decision_explicitness_distribution']:
    con.execute(f"DROP TABLE IF EXISTS {tname}")

con.execute("""
    CREATE TABLE v_anchor_quality_recode_distribution AS
    SELECT anchor_quality_recode, count(*) as blocks,
           round(count(*) * 100.0 / sum(count(*)) over (), 2) as pct
    FROM decision_blocks_resolved GROUP BY anchor_quality_recode
""")
con.execute("""
    CREATE TABLE v_anchor_resolution_status_distribution AS
    SELECT anchor_resolution_status, count(*) as blocks,
           round(count(*) * 100.0 / sum(count(*)) over (), 2) as pct
    FROM decision_blocks_resolved GROUP BY anchor_resolution_status
""")
con.execute("""
    CREATE TABLE v_decision_explicitness_distribution AS
    SELECT decision_explicitness, count(*) as blocks,
           round(count(*) * 100.0 / sum(count(*)) over (), 2) as pct
    FROM decision_blocks_resolved GROUP BY decision_explicitness
""")

# Drop backup
con.execute("DROP TABLE IF EXISTS decision_blocks_resolved_backup")

con.commit()

# ═══════════════════════════════════════════
# 4. VERIFICATION
# ═══════════════════════════════════════════

total = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved").fetchone()[0]
cf_total = con.execute("SELECT COUNT(DISTINCT anchor_slug) FROM decision_blocks_resolved WHERE namespace = 'cf'").fetchone()[0]
adct_total = con.execute("SELECT COUNT(DISTINCT anchor_slug) FROM decision_blocks_resolved WHERE namespace = 'adct'").fetchone()[0]
normativos = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE decision_unit_type = 'dispositivo_normativo'").fetchone()[0]
stf_blocks = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE anchor_source = 'stf_import'").fetchone()[0]

import os
print(f"\n{'='*60}")
print(f"  BANCO COMPLETO")
print(f"{'='*60}")
print(f"  Total blocos: {total}")
print(f"  CF artigos: {cf_total} / 250")
print(f"  ADCT artigos: {adct_total} / 138")
print(f"  Total artigos: {cf_total + adct_total} / 388")
print(f"")
print(f"  STF decisions: {stf_blocks}")
print(f"  Dispositivos normativos (sem decisão): {normativos}")
print(f"")
print(f"  CF com decisões: {cf_with_decisions}")
print(f"  CF sem decisões: {cf_empty}")
print(f"  ADCT com decisões: {adct_with_decisions}")
print(f"  ADCT sem decisões: {adct_empty}")
print(f"")
print(f"  DB: {DB_PATH} ({os.path.getsize(str(DB_PATH))/1024/1024:.1f} MB)")

con.close()
print("\nDone.")
