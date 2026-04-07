"""
Importação hierárquica: STF decisions ancoradas a sub-dispositivos exatos.
Slug completo: cf-1988-art-5-inc-x, cf-1988-art-37-par-2-inc-iii-ali-b
Estrutura normativa completa do Planalto (250 CF + 138 ADCT).
"""
import re
import sqlite3
import hashlib
from collections import defaultdict
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
PLANALTO_PATH = Path(r"C:\projetos\icons\ingest\cf_planalto.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")

stf_html = HTML_PATH.read_text(encoding="utf-8", errors="replace")
with open(PLANALTO_PATH, 'rb') as f:
    planalto_html = f.read().decode('latin-1')

# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════

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

RE_ROMAN = re.compile(r'^(X{0,3}(?:IX|IV|V?I{0,3}))\b', re.IGNORECASE)
RE_PAR = re.compile(r'(?:§|Par[áa]grafo)\s*(?:[úu]nico|(\d+))', re.IGNORECASE)
RE_ALI = re.compile(r'^([a-z])\)')

CLASSES_PROC = r'ADI|ADC|ADPF|ADO|RE|ARE|HC|RHC|MS|MI|AP|ACO|Rcl|AI|Pet|SS|SL|IF|Inq|Ext|AC|AgR|ED|MC|QO|SV|PSV|AO|AR|RMS|CR|Rp|STA'
RE_PROC = re.compile(rf'\b({CLASSES_PROC})\s*[\-n.\s]*([\d][\d.,]*)', re.IGNORECASE)
RE_REL = re.compile(r'rel\.?\s*(?:p/\s*o?\s*ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_RED = re.compile(r'red\.?\s*(?:do\s+ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_JULG = re.compile(r'j\.\s*(\d[\d\-/]+(?:\s*de\s*\w+\s*de\s*\d+)?)', re.IGNORECASE)
RE_DJE = re.compile(r'D[Jj][Ee]?\s*de\s*(\d[\d\-/]+)', re.IGNORECASE)
RE_TEMA = re.compile(r'[Tt]ema\s*(\d+)')

EDITORIAL_PREFIXES = [
    'Controle concentrado de constitucionalidade',
    'Controle de concentrado de constitucionalidade',
    'Repercussão geral', 'Repercussão Geral',
    'Súmula Vinculante', 'Súmula vinculante',
    'Julgados correlatos', 'Julgado correlato',
    'Julgados Correlatos', 'Julgado Correlato',
    'Súmula', 'Preâmbulo',
]

def detect_editorial(text, current):
    t = text.lower()
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
    return current

def extract_meta(text):
    meta = {'process_class': '', 'process_number': '', 'relator': '',
            'redator': '', 'julgamento_data': '', 'dje_data': '', 'tema_rg': ''}
    if not text: return meta
    m = RE_PROC.search(text)
    if m:
        meta['process_class'] = m.group(1).upper()
        meta['process_number'] = m.group(2).replace('.', '').replace(',', '')
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
    return meta

def classify_unit_type(ed, meta_text, pc, tema):
    e = (ed or '').lower()
    if tema: return 'repercussao_geral'
    if 'sumula_vinculante' in e: return 'sumula_vinculante'
    if 'sumula' in e: return 'sumula'
    if 'controle_concentrado' in e: return 'controle_concentrado'
    if 'repercussao_geral' in e: return 'repercussao_geral'
    if 'julgados_correlatos' in e: return 'julgado_correlato'
    if pc: return 'julgado_principal'
    return 'comentario_editorial'

def extract_sub_ident(dtype, label):
    """Extract identifier from sub-device label."""
    if dtype == 'inc':
        m = RE_ROMAN.match(label)
        return m.group(1).lower() if m else None
    elif dtype == 'par':
        m = RE_PAR.search(label)
        if m:
            return m.group(1) if m.group(1) else 'unico'
        return None
    elif dtype == 'ali':
        m = RE_ALI.match(label)
        return m.group(1) if m else None
    return None


# ═══════════════════════════════════════════
# 1. BUILD DEVICE HIERARCHY FROM STF HTML
# ═══════════════════════════════════════════

print("Building device hierarchy from STF HTML...")

# ADCT boundary
adct_start = None
seen_art1 = False
for m in re.finditer(r'id="(art\d+[a-z]*)"', stf_html):
    w = stf_html[max(0, m.start()-500):m.start()+500]
    nm = re.search(r'Art\.?\s*(\d+)', w)
    if nm and int(nm.group(1)) == 1:
        if seen_art1:
            adct_start = m.start()
            break
        seen_art1 = True

print(f"  ADCT boundary: {adct_start}")

# Collect all positioned elements: art, inc, par, ali, com
elements = []

for m in re.finditer(r'id="(art)(\d+[a-z]*)"', stf_html):
    pos = m.start()
    w = stf_html[max(0, pos-500):pos+500]
    nm = re.search(r'Art\.?\s*(\d+)', w)
    if not nm: continue
    is_adct = adct_start and pos >= adct_start
    elements.append((pos, 'art', m.group(1)+m.group(2), int(nm.group(1)), is_adct))

for m in re.finditer(r'id="(inc|par|ali)(\d+[a-z]*)"', stf_html):
    pos = m.start()
    dtype = m.group(1)
    did = m.group(1) + m.group(2)
    chunk = stf_html[pos:pos+400]
    label_m = re.search(r'>([^<]{1,300})</', chunk)
    label = strip_html(label_m.group(1))[:100] if label_m else ''
    ident = extract_sub_ident(dtype, label)
    is_adct = adct_start and pos >= adct_start
    elements.append((pos, dtype, did, ident, is_adct))

# Comments
for m in re.finditer(r'<div\s+class="com"\s+id="com(\d+)"[^>]*>(.*?)</div>', stf_html, re.DOTALL):
    elements.append((m.start(), 'com', int(m.group(1)), m.group(2), None))

elements.sort(key=lambda x: x[0])

# Walk elements and build slug for each comment
print("  Assigning hierarchical slugs to comments...")

current_art = None
current_art_num = None
current_is_adct = False
# Stack: [(type, ident)] for nested sub-devices
# par resets inc context, inc resets ali context
current_par = None  # (ident)
current_inc = None  # (ident)
current_ali = None  # (ident)
current_editorial = ''
last_com_end = 0

blocks = []

for el in elements:
    pos = el[0]
    etype = el[1]

    if etype == 'art':
        _, _, aid, art_num, is_adct = el
        current_art = aid
        current_art_num = art_num
        current_is_adct = is_adct
        current_par = None
        current_inc = None
        current_ali = None
        current_editorial = ''

    elif etype == 'par':
        _, _, did, ident, is_adct = el
        current_par = ident
        current_inc = None  # reset: new paragraph starts fresh
        current_ali = None

    elif etype == 'inc':
        _, _, did, ident, is_adct = el
        current_inc = ident
        current_ali = None  # reset

    elif etype == 'ali':
        _, _, did, ident, is_adct = el
        current_ali = ident

    elif etype == 'com':
        _, _, com_id, raw_html, _ = el
        if current_art_num is None:
            continue

        # Build slug
        prefix = 'adct' if current_is_adct else 'cf-1988'
        slug = f"{prefix}-art-{current_art_num}"

        if current_par:
            slug += f"-par-{current_par}"
        if current_inc:
            slug += f"-inc-{current_inc}"
        if current_ali:
            slug += f"-ali-{current_ali}"

        # Detect editorial
        raw_text = strip_html(raw_html)
        current_editorial = detect_editorial(raw_text[:80], current_editorial)

        # Strip editorial prefix
        for pfx in EDITORIAL_PREFIXES:
            if raw_text.startswith(pfx):
                raw_text = raw_text[len(pfx):].strip()
                break

        # Split text / metadata
        meta_match = re.search(r'\[([^\]]{10,})\]\s*$', raw_text)
        if meta_match:
            metadata_text = meta_match.group(1).strip()
            block_text = raw_text[:meta_match.start()].strip()
        else:
            metadata_text = ''
            block_text = raw_text

        meta = extract_meta(metadata_text or block_text[:200])
        pc = meta['process_class']
        pn = meta['process_number']
        pk = f"{pc}_{pn}" if pc and pn else (pn or pc or None)
        dut = classify_unit_type(current_editorial, metadata_text, pc, meta['tema_rg'])
        bh = hashlib.md5(f"{slug}|{current_editorial}|{(block_text or '')[:200]}".encode()).hexdigest()[:16]
        ns = 'adct' if current_is_adct else 'cf'

        blocks.append({
            'anchor_slug': slug,
            'anchor_label': f"Art. {current_art_num}" + (' (ADCT)' if current_is_adct else ''),
            'anchor_node_type': 'artigo',
            'anchor_quality': 'exact',
            'anchor_confidence': 1.0,
            'anchor_source': 'stf_import',
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
            'tema_rg': meta['tema_rg'],
            'block_hash': bh,
            'stf_com_id': com_id,
            'anchor_quality_recode': 'exact',
            'anchor_resolution_status': 'resolved',
            'decision_explicitness': 'explicit',
        })

print(f"  Blocks with hierarchical slugs: {len(blocks)}")

# Stats
unique_slugs = set(b['anchor_slug'] for b in blocks)
print(f"  Unique slugs: {len(unique_slugs)}")
with_sub = sum(1 for s in unique_slugs if '-inc-' in s or '-par-' in s or '-ali-' in s)
print(f"  Slugs with sub-devices: {with_sub}")

# ═══════════════════════════════════════════
# 2. PLANALTO NORMATIVE TEXT
# ═══════════════════════════════════════════

print("\nParsing Planalto for normative text...")
planalto_adct = 1069024

cf_norms = {}
adct_norms = {}
for m in re.finditer(r'Art\.\s*(\d+)[^\n<]{0,500}', planalto_html, re.DOTALL):
    num = int(m.group(1))
    end = min(m.start() + 1000, len(planalto_html))
    next_a = re.search(r'Art\.\s*\d+', planalto_html[m.start()+10:end])
    if next_a:
        end = min(end, m.start() + 10 + next_a.start())
    label = strip_html(planalto_html[m.start():end])[:200]
    if m.start() < planalto_adct:
        if num not in cf_norms: cf_norms[num] = label
    else:
        if num not in adct_norms: adct_norms[num] = label

print(f"  CF norms: {len(cf_norms)}, ADCT norms: {len(adct_norms)}")

# ═══════════════════════════════════════════
# 3. REBUILD DATABASE
# ═══════════════════════════════════════════

print("\nRebuilding database...")
con = sqlite3.connect(str(DB_PATH))

for vname in con.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall():
    con.execute(f"DROP VIEW IF EXISTS [{vname[0]}]")

con.execute("DROP TABLE IF EXISTS decision_blocks_resolved_backup")
con.execute("ALTER TABLE decision_blocks_resolved RENAME TO decision_blocks_resolved_backup")

con.execute("""
CREATE TABLE decision_blocks_resolved (
    block_id INTEGER PRIMARY KEY, paragraph_start INTEGER, paragraph_end INTEGER,
    anchor_slug TEXT, anchor_label TEXT, anchor_node_type TEXT,
    anchor_quality TEXT, anchor_confidence REAL, anchor_source TEXT,
    matched_variant TEXT, variant_origin TEXT, match_priority INTEGER,
    context_relation TEXT, namespace TEXT,
    editorial_marker TEXT, editorial_label TEXT, decision_unit_type TEXT,
    block_text TEXT, metadata_text TEXT,
    process_class TEXT, process_number TEXT, process_key TEXT,
    relator TEXT, redator TEXT, julgamento_data TEXT, dje_data TEXT,
    tema_rg TEXT, sumula_num TEXT, raw_signature TEXT, block_hash TEXT,
    anchor_quality_recode TEXT, anchor_resolution_status TEXT,
    decision_explicitness TEXT, stf_com_id INTEGER,
    normative_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Group STF blocks by article
stf_cf = defaultdict(list)
stf_adct = defaultdict(list)
for b in blocks:
    m = re.match(r'cf-1988-art-(\d+)', b['anchor_slug'])
    if m: stf_cf[int(m.group(1))].append(b)
    m = re.match(r'adct-art-(\d+)', b['anchor_slug'])
    if m: stf_adct[int(m.group(1))].append(b)

cols = [
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
ph = ','.join('?' for _ in cols)
sql = f"INSERT INTO decision_blocks_resolved ({','.join(cols)}) VALUES ({ph})"

state = {'bid': 1}
cf_w = cf_e = adct_w = adct_e = 0

def insert_decisions(art_num, decisions, normative, ns, is_adct):
    bid = state['bid']
    prefix = 'adct' if is_adct else 'cf-1988'
    base_slug = f"{prefix}-art-{art_num}"
    label = f"Art. {art_num}" + (' (ADCT)' if is_adct else '')

    if decisions:
        for d in decisions:
            vals = [
                bid, None, None, d['anchor_slug'],
                label, 'artigo', d['anchor_quality'], d['anchor_confidence'],
                d['anchor_source'], '', '', None,
                d.get('editorial_marker', ''), ns,
                d.get('editorial_marker', ''), d.get('editorial_label', ''),
                d['decision_unit_type'], d['block_text'], d['metadata_text'],
                d.get('process_class', ''), d.get('process_number', ''), d.get('process_key'),
                d.get('relator', ''), d.get('redator', ''), d.get('julgamento_data', ''), d.get('dje_data', ''),
                d.get('tema_rg', ''), '', f"{d.get('process_class','')} {d.get('process_number','')} rel. {d.get('relator','')}".strip(),
                d['block_hash'], d['anchor_quality_recode'], d['anchor_resolution_status'],
                d['decision_explicitness'], d['stf_com_id'], normative
            ]
            con.execute(sql, vals)
            bid += 1
        state['bid'] = bid
        return True
    else:
        bh = hashlib.md5(f"{base_slug}|normativo|{(normative or '')[:100]}".encode()).hexdigest()[:16]
        vals = [
            bid, None, None, base_slug,
            label, 'artigo', 'normativo', 1.0,
            'planalto', '', '', None,
            '', ns, '', '',
            'dispositivo_normativo', '', '',
            '', '', None,
            '', '', '', '',
            '', '', '', bh,
            'normativo', 'resolved', '',
            None, normative
        ]
        con.execute(sql, vals)
        bid += 1
        state['bid'] = bid
        return False

# CF 1-250
for n in range(1, 251):
    norm = cf_norms.get(n, f"Art. {n}")
    has = insert_decisions(n, stf_cf.get(n, []), norm, 'cf', False)
    if has: cf_w += 1
    else: cf_e += 1

# ADCT 1-138
for n in range(1, 139):
    norm = adct_norms.get(n, f"Art. {n} (ADCT)")
    has = insert_decisions(n, stf_adct.get(n, []), norm, 'adct', True)
    if has: adct_w += 1
    else: adct_e += 1

# Indexes
for c in ['anchor_slug', 'anchor_quality', 'relator', 'process_key',
          'decision_unit_type', 'process_class', 'namespace', 'anchor_source',
          'anchor_quality_recode', 'editorial_marker', 'stf_com_id']:
    con.execute(f"CREATE INDEX IF NOT EXISTS idx_dbr_{c} ON decision_blocks_resolved({c})")

# block_anchors
con.execute("DROP TABLE IF EXISTS block_anchors")
con.execute("""CREATE TABLE block_anchors (
    id INTEGER PRIMARY KEY AUTOINCREMENT, block_id INTEGER NOT NULL,
    anchor_slug TEXT NOT NULL, anchor_role TEXT DEFAULT 'primary',
    confidence REAL, source TEXT)""")
con.execute("""INSERT INTO block_anchors (block_id, anchor_slug, anchor_role, confidence, source)
    SELECT block_id, anchor_slug, 'primary', anchor_confidence, anchor_source
    FROM decision_blocks_resolved WHERE anchor_slug IS NOT NULL""")
con.execute("CREATE INDEX idx_ba_block ON block_anchors(block_id)")
con.execute("CREATE INDEX idx_ba_slug ON block_anchors(anchor_slug)")

# Materialized views
for t in ['v_anchor_quality_recode_distribution', 'v_anchor_resolution_status_distribution',
          'v_decision_explicitness_distribution']:
    con.execute(f"DROP TABLE IF EXISTS {t}")
con.execute("""CREATE TABLE v_anchor_quality_recode_distribution AS
    SELECT anchor_quality_recode, count(*) as blocks, round(count(*)*100.0/sum(count(*)) over(),2) as pct
    FROM decision_blocks_resolved GROUP BY anchor_quality_recode""")
con.execute("""CREATE TABLE v_anchor_resolution_status_distribution AS
    SELECT anchor_resolution_status, count(*) as blocks, round(count(*)*100.0/sum(count(*)) over(),2) as pct
    FROM decision_blocks_resolved GROUP BY anchor_resolution_status""")
con.execute("""CREATE TABLE v_decision_explicitness_distribution AS
    SELECT decision_explicitness, count(*) as blocks, round(count(*)*100.0/sum(count(*)) over(),2) as pct
    FROM decision_blocks_resolved GROUP BY decision_explicitness""")

con.execute("DROP TABLE IF EXISTS decision_blocks_resolved_backup")
con.commit()

# ═══════════════════════════════════════════
# 4. VERIFY
# ═══════════════════════════════════════════

total = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved").fetchone()[0]
cf_slugs = con.execute("SELECT COUNT(DISTINCT anchor_slug) FROM decision_blocks_resolved WHERE namespace='cf'").fetchone()[0]
adct_slugs = con.execute("SELECT COUNT(DISTINCT anchor_slug) FROM decision_blocks_resolved WHERE namespace='adct'").fetchone()[0]
stf_n = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE anchor_source='stf_import'").fetchone()[0]
norm_n = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE decision_unit_type='dispositivo_normativo'").fetchone()[0]
sub_slugs = con.execute("SELECT COUNT(DISTINCT anchor_slug) FROM decision_blocks_resolved WHERE anchor_slug LIKE '%-inc-%' OR anchor_slug LIKE '%-par-%' OR anchor_slug LIKE '%-ali-%'").fetchone()[0]

import os
print(f"\n{'='*60}")
print(f"  BANCO COMPLETO — HIERÁRQUICO")
print(f"{'='*60}")
print(f"  Total blocos: {total}")
print(f"  CF artigos: 250/250 ({cf_w} com decisões, {cf_e} sem)")
print(f"  ADCT artigos: 138/138 ({adct_w} com decisões, {adct_e} sem)")
print(f"  Slugs únicos: CF={cf_slugs} ADCT={adct_slugs}")
print(f"  Slugs com sub-dispositivo: {sub_slugs}")
print(f"  STF decisions: {stf_n}")
print(f"  Dispositivos normativos: {norm_n}")

print(f"\n  Amostra Art. 5:")
for r in con.execute("""SELECT anchor_slug, editorial_marker, decision_unit_type, substr(block_text,1,50)
    FROM decision_blocks_resolved WHERE anchor_slug LIKE 'cf-1988-art-5%' LIMIT 10""").fetchall():
    print(f"    {r[0]:35s} | {(r[1] or ''):20s} | {r[2]:20s} | {(r[3] or '')[:40]}")

print(f"\n  DB: {DB_PATH} ({os.path.getsize(str(DB_PATH))/1024/1024:.1f} MB)")
con.close()
print("\nDone.")
