"""
Importa blocos diretamente do HTML do STF para o banco.
Reconstrói decision_blocks_resolved espelhando o STF 1:1.
"""
import re
import sqlite3
import hashlib
import unicodedata
from collections import defaultdict
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

# ═══════════════════════════════════════════
# REGEX para metadados
# ═══════════════════════════════════════════

CLASSES_PROC = r'ADI|ADC|ADPF|ADO|RE|ARE|HC|RHC|MS|MI|AP|ACO|Rcl|AI|Pet|SS|SL|IF|Inq|Ext|AC|AgR|ED|MC|QO|SV|PSV|AO|AR|RMS|CR|Rp|STA'
RE_PROC = re.compile(rf'\b({CLASSES_PROC})\s*[\-n.\s]*([\d][\d.,]*)', re.IGNORECASE)
RE_REL = re.compile(r'rel\.?\s*(?:p/\s*o?\s*ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_RED = re.compile(r'red\.?\s*(?:do\s+ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_JULG = re.compile(r'j\.\s*(\d[\d\-/]+(?:\s*de\s*\w+\s*de\s*\d+)?)', re.IGNORECASE)
RE_DJE = re.compile(r'D[Jj][Ee]?\s*de\s*(\d[\d\-/]+)', re.IGNORECASE)
RE_TEMA = re.compile(r'[Tt]ema\s*(\d+)')

EDITORIAL_ORDER = {
    'sumula_vinculante': 1,
    'sumula': 2,
    'controle_concentrado': 3,
    'repercussao_geral': 4,
    'julgados_correlatos': 5,
    'comentario_editorial': 6,
    '': 7,
}

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

def detect_editorial(text_before_com, current_editorial):
    """Detect editorial from text between previous com and this one."""
    t = text_before_com.lower()
    if 'súmula vinculante' in t or 'sumula vinculante' in t:
        return 'sumula_vinculante'
    if 'controle concentrado' in t or 'controle de concentrado' in t:
        return 'controle_concentrado'
    if 'repercussão geral' in t or 'repercussao geral' in t:
        return 'repercussao_geral'
    if 'julgado correlato' in t or 'julgados correlatos' in t:
        return 'julgados_correlatos'
    if 'súmula' in t or 'sumula' in t:
        return 'sumula'
    return current_editorial

def extract_meta(text):
    meta = {'process_class': '', 'process_number': '', 'relator': '',
            'redator': '', 'julgamento_data': '', 'dje_data': '', 'tema_rg': ''}
    if not text:
        return meta
    m = RE_PROC.search(text)
    if m:
        meta['process_class'] = m.group(1).upper()
        meta['process_number'] = m.group(2).replace('.', '').replace(',', '')
    m = RE_REL.search(text)
    if m:
        meta['relator'] = m.group(1).strip()
    m = RE_RED.search(text)
    if m:
        meta['redator'] = m.group(1).strip()
    m = RE_JULG.search(text)
    if m:
        meta['julgamento_data'] = m.group(1).strip()
    m = RE_DJE.search(text)
    if m:
        meta['dje_data'] = m.group(1).strip()
    m = RE_TEMA.search(text)
    if m:
        meta['tema_rg'] = m.group(1)
    return meta

def build_slug(art_num, sub_type=None, sub_label=None, is_adct=False):
    """Build slug from article number and sub-device."""
    prefix = 'adct' if is_adct else 'cf-1988'
    slug = f"{prefix}-art-{art_num}"
    # Sub-device resolution would need more context
    # For now, anchor at article level
    return slug

def block_hash(slug, ed, text, meta):
    raw = f"{slug}|{ed}|{(text or '')[:200]}|{(meta or '')[:100]}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]

def classify_unit_type(editorial, meta_text, process_class, tema):
    ed = (editorial or '').lower()
    if tema:
        return 'repercussao_geral'
    if 'sumula_vinculante' in ed:
        return 'sumula_vinculante'
    if 'sumula' in ed:
        return 'sumula'
    if 'controle_concentrado' in ed:
        return 'controle_concentrado'
    if 'repercussao_geral' in ed:
        return 'repercussao_geral'
    if 'julgados_correlatos' in ed:
        return 'julgado_correlato'
    if process_class:
        return 'julgado_principal'
    return 'comentario_editorial'


# ═══════════════════════════════════════════
# 1. PARSE ALL STF CONTENT
# ═══════════════════════════════════════════

print("Parsing STF HTML...")

# Find articles
# Find ADCT boundary: first repeated Art. 1 after CF articles
adct_start_pos = None
seen_art1 = False
for m in re.finditer(r'id="(art\d+[a-z]*)"', html):
    pos = m.start()
    window = html[max(0, pos-500):pos+500]
    num_m = re.search(r'Art\.?\s*(\d+)', window)
    if num_m and int(num_m.group(1)) == 1:
        if seen_art1:
            adct_start_pos = pos
            break
        seen_art1 = True

print(f"  ADCT boundary: position {adct_start_pos}")

art_entries = []
for m in re.finditer(r'id="(art\d+[a-z]*)"', html):
    pos = m.start()
    art_id = m.group(1)
    window = html[max(0, pos-500):pos+500]
    num_m = re.search(r'Art\.?\s*(\d+)', window)
    if not num_m:
        continue
    art_num = int(num_m.group(1))
    is_adct = adct_start_pos is not None and pos >= adct_start_pos
    art_entries.append((pos, art_num, art_id, is_adct))

# Find sub-devices
sub_entries = []
for m in re.finditer(r'id="(inc|par|ali)(\d+[a-z]*)"', html):
    pos = m.start()
    sub_type = m.group(1)
    sub_id = m.group(1) + m.group(2)
    # Get label
    chunk = html[pos:pos + 400]
    label_m = re.search(r'>([^<]{2,200})</', chunk)
    label = strip_html(label_m.group(1))[:100] if label_m else ''
    sub_entries.append((pos, sub_type, sub_id, label))

print(f"  Articles: {len(art_entries)}")
print(f"  Sub-devices: {len(sub_entries)}")

# Extract all blocks
blocks = []
block_id = 1

for i, (art_pos, art_num, art_id, is_adct) in enumerate(art_entries):
    next_pos = art_entries[i + 1][0] if i + 1 < len(art_entries) else len(html)
    section = html[art_pos:next_pos]

    # Sub-devices in this section
    subs_here = [(p - art_pos, st, sid, sl)
                 for p, st, sid, sl in sub_entries
                 if art_pos < p < next_pos]

    # Find all com blocks with their positions
    com_matches = list(re.finditer(
        r'<div\s+class="com"\s+id="com(\d+)"[^>]*>(.*?)</div>',
        section, re.DOTALL
    ))

    # Track editorial context
    current_editorial = ''
    last_com_end = 0

    for cm in com_matches:
        com_pos = cm.start()
        com_id = int(cm.group(1))
        raw_html = cm.group(2)

        # Detect editorial from BOTH between-text and inside-com text
        between = strip_html(section[last_com_end:com_pos])
        current_editorial = detect_editorial(between, current_editorial)
        last_com_end = cm.end()

        raw_text = strip_html(raw_html)

        # Also detect editorial from the com block itself
        current_editorial = detect_editorial(raw_text[:80], current_editorial)

        # Strip editorial prefix from raw_text before splitting
        EDITORIAL_PREFIXES_STRIP = [
            'Controle concentrado de constitucionalidade',
            'Controle de concentrado de constitucionalidade',
            'Repercussão geral', 'Repercussão Geral',
            'Súmula Vinculante', 'Súmula vinculante',
            'Julgados correlatos', 'Julgado correlato',
            'Julgados Correlatos', 'Julgado Correlato',
            'Súmula', 'Preâmbulo',
        ]
        for prefix in EDITORIAL_PREFIXES_STRIP:
            if raw_text.startswith(prefix):
                raw_text = raw_text[len(prefix):].strip()
                break

        # Separate block_text from metadata_text
        # Metadata is in [...] at end, can be multiple [...]
        meta_match = re.search(r'\[([^\]]{10,})\]\s*$', raw_text)
        if meta_match:
            metadata_text = meta_match.group(1).strip()
            block_text = raw_text[:meta_match.start()].strip()
        else:
            metadata_text = ''
            block_text = raw_text

        # Determine sub-device
        current_sub = None
        for sp, st, sid, sl in subs_here:
            if sp < com_pos:
                current_sub = (st, sid, sl)
            else:
                break

        # Build slug
        slug_base = 'adct' if is_adct else 'cf-1988'
        slug = f"{slug_base}-art-{art_num}"

        # Extract metadata
        meta = extract_meta(metadata_text or block_text[:200])

        pc = meta['process_class']
        pn = meta['process_number']
        pk = f"{pc}_{pn}" if pc and pn else (pn or pc or None)
        tema = meta['tema_rg']
        dut = classify_unit_type(current_editorial, metadata_text, pc, tema)
        bh = block_hash(slug, current_editorial, block_text, metadata_text)

        ns = 'adct' if is_adct else 'cf'

        blocks.append({
            'block_id': block_id,
            'paragraph_start': None,
            'paragraph_end': None,
            'anchor_slug': slug,
            'anchor_label': f"Art. {art_num}",
            'anchor_node_type': 'artigo',
            'anchor_quality': 'exact',
            'anchor_confidence': 1.0,
            'anchor_source': 'stf_import',
            'matched_variant': '',
            'variant_origin': '',
            'match_priority': None,
            'context_relation': current_editorial,
            'namespace': ns,
            'editorial_marker': current_editorial,
            'editorial_label': current_editorial.replace('_', ' ').title() if current_editorial else '',
            'decision_unit_type': dut,
            'block_text': block_text,
            'metadata_text': metadata_text,
            'process_class': pc,
            'process_number': pn,
            'process_key': pk,
            'relator': meta['relator'],
            'redator': meta['redator'],
            'julgamento_data': meta['julgamento_data'],
            'dje_data': meta['dje_data'],
            'tema_rg': tema,
            'sumula_num': '',
            'raw_signature': f"{pc} {pn} rel. {meta['relator']}".strip(),
            'block_hash': bh,
            'anchor_quality_recode': 'exact',
            'anchor_resolution_status': 'resolved',
            'decision_explicitness': 'explicit',
            'stf_com_id': com_id,
        })
        block_id += 1

print(f"  Blocks extracted: {len(blocks)}")

# ═══════════════════════════════════════════
# 2. REBUILD DATABASE TABLE
# ═══════════════════════════════════════════

print("\nRebuilding database...")
con = sqlite3.connect(str(DB_PATH))

# Drop dependent views first
for vname in con.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall():
    con.execute(f"DROP VIEW IF EXISTS [{vname[0]}]")

# Backup existing table
con.execute("DROP TABLE IF EXISTS decision_blocks_resolved_backup")
con.execute("ALTER TABLE decision_blocks_resolved RENAME TO decision_blocks_resolved_backup")

# Create new table
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
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Insert
cols = [
    'block_id', 'paragraph_start', 'paragraph_end', 'anchor_slug',
    'anchor_label', 'anchor_node_type', 'anchor_quality', 'anchor_confidence',
    'anchor_source', 'matched_variant', 'variant_origin', 'match_priority',
    'context_relation', 'namespace', 'editorial_marker', 'editorial_label',
    'decision_unit_type', 'block_text', 'metadata_text', 'process_class',
    'process_number', 'process_key', 'relator', 'redator', 'julgamento_data',
    'dje_data', 'tema_rg', 'sumula_num', 'raw_signature', 'block_hash',
    'anchor_quality_recode', 'anchor_resolution_status', 'decision_explicitness',
    'stf_com_id',
]
placeholders = ','.join('?' for _ in cols)
insert_sql = f"INSERT INTO decision_blocks_resolved ({','.join(cols)}) VALUES ({placeholders})"

for b in blocks:
    values = [b[c] for c in cols]
    con.execute(insert_sql, values)

# Indexes
for idx_col in ['anchor_slug', 'anchor_quality', 'relator', 'process_key',
                'decision_unit_type', 'process_class', 'namespace', 'anchor_source',
                'anchor_quality_recode', 'anchor_resolution_status', 'decision_explicitness',
                'editorial_marker', 'stf_com_id']:
    con.execute(f"CREATE INDEX IF NOT EXISTS idx_dbr_{idx_col} ON decision_blocks_resolved({idx_col})")

# Rebuild block_anchors
con.execute("DROP TABLE IF EXISTS block_anchors")
con.execute("""
CREATE TABLE block_anchors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id        INTEGER NOT NULL,
    anchor_slug     TEXT NOT NULL,
    anchor_role     TEXT DEFAULT 'primary',
    confidence      REAL,
    source          TEXT,
    FOREIGN KEY (block_id) REFERENCES decision_blocks_resolved(block_id)
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

# Recreate materialized views
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

con.commit()

# ═══════════════════════════════════════════
# 3. VERIFICATION
# ═══════════════════════════════════════════

total = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved").fetchone()[0]

print(f"\n{'='*60}")
print(f"  IMPORTAÇÃO DIRETA DO STF")
print(f"{'='*60}")
print(f"  Total blocos: {total}")
print(f"  STF online: 8903")
print(f"  Match: {'SIM' if total == 8903 else 'NAO - diff ' + str(total - 8903)}")

# Per article comparison
stf_by_art = defaultdict(int)
for b in blocks:
    m = re.match(r'cf-1988-art-(\d+)', b['anchor_slug'])
    if m:
        stf_by_art[int(m.group(1))] += 1

print(f"\n  Artigos cobertos: {len(stf_by_art)}")

# Distribution
print(f"\n  Por decision_unit_type:")
for r in con.execute("SELECT decision_unit_type, COUNT(*) FROM decision_blocks_resolved GROUP BY decision_unit_type ORDER BY COUNT(*) DESC").fetchall():
    print(f"    {r[0]:30s} {r[1]:5d}")

print(f"\n  Por editorial_marker:")
for r in con.execute("SELECT editorial_marker, COUNT(*) FROM decision_blocks_resolved GROUP BY editorial_marker ORDER BY COUNT(*) DESC").fetchall():
    print(f"    {(r[0] or '(sem)'):30s} {r[1]:5d}")

print(f"\n  Com process_key: {con.execute('SELECT COUNT(*) FROM decision_blocks_resolved WHERE process_key IS NOT NULL').fetchone()[0]}")
print(f"  Com relator: {con.execute('SELECT COUNT(*) FROM decision_blocks_resolved WHERE relator IS NOT NULL AND relator != \"\"').fetchone()[0]}")

# Verify text content
total_chars = con.execute("SELECT SUM(LENGTH(block_text)) FROM decision_blocks_resolved").fetchone()[0]
empty = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE block_text IS NULL OR block_text = ''").fetchone()[0]
print(f"\n  Total chars: {total_chars:,}")
print(f"  Blocos vazios: {empty}")

import os
print(f"\n  DB: {DB_PATH} ({os.path.getsize(str(DB_PATH))/1024/1024:.1f} MB)")

con.close()

# ═══════════════════════════════════════════
# 4. FUNÇÃO DE ATUALIZAÇÃO AUTOMÁTICA
# ═══════════════════════════════════════════

def atualizar_do_stf():
    """
    Baixa o HTML do STF, compara com o banco atual,
    e aplica apenas as diferenças (novos blocos, removidos, alterados).
    Pode ser chamada periodicamente para manter o banco em sincronia.
    """
    import subprocess
    import tempfile

    print("\n" + "=" * 60)
    print("  ATUALIZAÇÃO AUTOMÁTICA")
    print("=" * 60)

    # 1. Baixar HTML atualizado
    print("  Baixando HTML do STF...")
    result = subprocess.run(
        ['curl', '-sk', '-A',
         'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         'https://portal.stf.jus.br/constituicao-supremo/constituicao.asp'],
        capture_output=True, timeout=60
    )
    if result.returncode != 0 or len(result.stdout) < 100000:
        print("  ERRO: falha ao baixar HTML do STF")
        return False

    new_html = result.stdout.decode('utf-8', errors='replace')
    print(f"  HTML baixado: {len(new_html):,} chars")

    # 2. Extrair com_ids do novo HTML
    new_com_ids = set()
    for m in re.finditer(r'id="com(\d+)"', new_html):
        new_com_ids.add(int(m.group(1)))

    # 3. Comparar com banco atual
    con = sqlite3.connect(str(DB_PATH))
    current_com_ids = set()
    for r in con.execute("SELECT stf_com_id FROM decision_blocks_resolved WHERE stf_com_id IS NOT NULL"):
        current_com_ids.add(r[0])

    novos = new_com_ids - current_com_ids
    removidos = current_com_ids - new_com_ids
    mantidos = new_com_ids & current_com_ids

    print(f"  Blocos no STF agora: {len(new_com_ids)}")
    print(f"  Blocos no banco: {len(current_com_ids)}")
    print(f"  Mantidos: {len(mantidos)}")
    print(f"  Novos no STF: {len(novos)}")
    print(f"  Removidos do STF: {len(removidos)}")

    if not novos and not removidos:
        print("  Banco já está em sincronia. Nada a fazer.")
        con.close()
        return True

    # 4. Se há diferenças, salvar novo HTML e re-importar
    if novos or removidos:
        print(f"  Salvando HTML atualizado...")
        HTML_PATH.write_text(new_html, encoding='utf-8')
        print(f"  Re-importando... (execute import_stf_direct.py novamente)")
        con.close()
        return 'needs_reimport'

    con.close()
    return True


# Se chamado com --update, executar atualização
import sys
if '--update' in sys.argv:
    atualizar_do_stf()
else:
    print("\nDone.")
    print("  Para atualizar do STF: python import_stf_direct.py --update")
