"""
Extração segura de metadados: só dados confirmados do HTML do STF.
Fontes (por ordem de confiança):
1. [referência bibliográfica] — estruturada, confiável
2. <a> link labels — classe processual confirmada
3. <a href> URL params — incidente/processo confirmado
4. Texto com padrões inequívocos — Súmula N, Tema N
"""
import re
import sqlite3
import csv
from collections import defaultdict
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

def strip_html(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'&ordm;', 'º', s); s = re.sub(r'&ordf;', 'ª', s)
    s = re.sub(r'&ldquo;', '"', s); s = re.sub(r'&rdquo;', '"', s)
    s = re.sub(r'&lsquo;', "'", s); s = re.sub(r'&rsquo;', "'", s)
    s = re.sub(r'&ndash;', '–', s); s = re.sub(r'&mdash;', '—', s)
    s = re.sub(r'&sect;', '§', s); s = re.sub(r'&amp;', '&', s)
    s = re.sub(r'&[a-z]+;', '', s)
    s = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# Regex
CLASSES = r'ADI|ADC|ADPF|ADO|RE|ARE|HC|RHC|MS|MI|AP|ACO|Rcl|AI|Pet|SS|SL|IF|Inq|Ext|AC|AgR|ED|MC|QO|SV|PSV|AO|AR|RMS|CR|Rp|STA|STP'
RE_PROC = re.compile(rf'\b({CLASSES})\s*[\-n.\s]*([\d][\d.,]*)', re.IGNORECASE)
RE_REL = re.compile(r'rel\.?\s*(?:p/\s*o?\s*ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_RED = re.compile(r'red\.?\s*(?:do\s+ac\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_VOTO = re.compile(r'voto\s+d[oa]\s*(?:rel\.?\s*)?min\.?\s*([^,\]\.\n]+)', re.IGNORECASE)
RE_JULG = re.compile(r'j\.\s*(\d[\d\-/]+(?:\s*(?:de\s*)?\w+\s*(?:de\s*)?\d{4})?)', re.IGNORECASE)
RE_DJE = re.compile(r'D[Jj][Ee]?\s*de\s*(\d[\d\-/]+(?:\s*(?:de\s*)?\w+\s*(?:de\s*)?\d{4})?)', re.IGNORECASE)
RE_DJ = re.compile(r'\bDJ\s+de\s*(\d[\d\-/]+)', re.IGNORECASE)
RE_TEMA = re.compile(r'[Tt]ema\s*(\d+)')
RE_SV = re.compile(r'S[uú]mula\s+Vinculante\s*n?[oº°]?\s*(\d+)', re.IGNORECASE)
RE_SUMULA = re.compile(r'S[uú]mula\s*n?[oº°]?\s*(\d+)', re.IGNORECASE)
RE_TURMA = re.compile(r'(\d)ª?\s*T\b|Plen[áa]rio|\bP\b,', re.IGNORECASE)
RE_MERITO = re.compile(r'com\s+m[ée]rito\s+julgado', re.IGNORECASE)
RE_PENDENTE = re.compile(r'm[ée]rito\s+pendente', re.IGNORECASE)

RELATOR_NORMALIZE = {
    'Roberto Barroso': 'Luís Roberto Barroso',
    'Marco Aurelio': 'Marco Aurélio',
    'Carmen Lúcia': 'Cármen Lúcia',
    'Carmén Lúcia': 'Cármen Lúcia',
    'Alexandre Moraes': 'Alexandre de Moraes',
    'Dias Tofolli': 'Dias Toffoli',
    'Sidney Sanches': 'Sydney Sanches',
    'Rosa Werber': 'Rosa Weber',
    'Carlos Britto': 'Ayres Britto',
}

def clean_name(name):
    if not name: return ''
    name = name.strip().rstrip('.-),;')
    name = re.split(r'[;\(\[\{]', name)[0].strip()
    words = name.split()
    if len(words) > 4: name = ' '.join(words[:4])
    name = RELATOR_NORMALIZE.get(name, name)
    return name if len(name) >= 4 else ''

def extract_from_ref(ref_text):
    """Extract structured metadata from a bracket reference. High confidence."""
    meta = {}

    m = RE_PROC.search(ref_text)
    if m:
        meta['process_class'] = m.group(1).upper()
        meta['process_number'] = m.group(2).replace('.', '').replace(',', '')

    m = RE_REL.search(ref_text)
    if m: meta['relator'] = clean_name(m.group(1))

    m = RE_RED.search(ref_text)
    if m: meta['redator'] = clean_name(m.group(1))

    if 'relator' not in meta:
        m = RE_VOTO.search(ref_text)
        if m: meta['relator'] = clean_name(m.group(1))

    m = RE_JULG.search(ref_text)
    if m: meta['julgamento_data'] = m.group(1).strip()

    m = RE_DJE.search(ref_text)
    if m:
        meta['dje_data'] = m.group(1).strip()
    else:
        m = RE_DJ.search(ref_text)
        if m: meta['dje_data'] = m.group(1).strip()

    m = RE_TEMA.search(ref_text)
    if m: meta['tema_rg'] = m.group(1)

    m = RE_TURMA.search(ref_text)
    if m:
        if m.group(1):
            meta['turma'] = f"{m.group(1)}ª T"
        elif 'plen' in m.group(0).lower():
            meta['turma'] = 'Plenário'
        else:
            meta['turma'] = 'P'

    if RE_MERITO.search(ref_text):
        meta['merito_status'] = 'julgado'
    elif RE_PENDENTE.search(ref_text):
        meta['merito_status'] = 'pendente'

    m = RE_SV.search(ref_text)
    if m:
        meta['sumula_num'] = m.group(1)
        meta['sumula_tipo'] = 'vinculante'
    else:
        m = RE_SUMULA.search(ref_text)
        if m:
            meta['sumula_num'] = m.group(1)
            meta['sumula_tipo'] = 'stf'

    return meta

def extract_from_links(raw_html):
    """Extract from <a> tags. Medium confidence."""
    meta = {}
    urls = re.findall(r'href="([^"]+)"', raw_html)
    link_labels = [strip_html(lt) for lt in re.findall(r'<a[^>]*>(.*?)</a>', raw_html, re.DOTALL)]

    combined_labels = ' '.join(link_labels)
    m = RE_PROC.search(combined_labels)
    if m:
        meta['process_class'] = m.group(1).upper()
        meta['process_number'] = m.group(2).replace('.', '').replace(',', '')

    # Extract tema from Repercussão Geral URLs
    for url in urls:
        tm = re.search(r'numeroTema=(\d+)', url)
        if tm: meta['tema_rg'] = tm.group(1)
        # Extract incidente from STF URLs
        inc = re.search(r'incidente=(\d+)', url)
        if inc: meta['stf_incidente'] = inc.group(1)

    meta['urls'] = urls
    meta['link_labels'] = link_labels
    return meta

def extract_from_text(text):
    """Extract only highly structured patterns from text. Low confidence but safe."""
    meta = {}
    # Only Súmula references (very structured)
    m = RE_SV.search(text)
    if m:
        meta['sumula_num'] = m.group(1)
        meta['sumula_tipo'] = 'vinculante'
    else:
        m = RE_SUMULA.search(text[:200])  # only in first 200 chars
        if m:
            meta['sumula_num'] = m.group(1)
            meta['sumula_tipo'] = 'stf'

    m = RE_TEMA.search(text)
    if m: meta['tema_rg'] = m.group(1)

    return meta


# ═══════════════════════════════════════════
# PARSE ALL COM BLOCKS
# ═══════════════════════════════════════════

print("Extracting confirmed metadata from STF HTML...")

# Build article map
adct_start = None
seen1 = False
for m in re.finditer(r'id="art\d+[a-z]*"', html):
    w = html[max(0, m.start()-500):m.start()+500]
    nm = re.search(r'Art\.?\s*(\d+)', w)
    if nm and int(nm.group(1)) == 1:
        if seen1: adct_start = m.start(); break
        seen1 = True

# Sub-devices for slug building
sub_stack = []
art_map = []
for m in re.finditer(r'id="(art|inc|par|ali)(\d+[a-z]*)"', html):
    pos = m.start()
    dtype = m.group(1)
    if dtype == 'art':
        w = html[max(0, pos-500):pos+500]
        nm = re.search(r'Art\.?\s*(\d+)', w)
        if nm:
            is_adct = adct_start and pos >= adct_start
            art_map.append((pos, int(nm.group(1)), is_adct))

results = []  # One row per com block

for cm in re.finditer(r'<div\s+class="com"\s+id="com(\d+)"[^>]*>(.*?)</div>', html, re.DOTALL):
    com_id = int(cm.group(1))
    raw = cm.group(2)
    com_pos = cm.start()
    text = strip_html(raw)

    # Skip editorial markers
    if len(text) < 80 and any(kw in text.lower() for kw in ['controle', 'repercuss', 'julgado', 'súmula', 'sumula', 'correlato']):
        continue

    # Find article
    art_num = None
    is_adct = False
    for pos, anum, adct in reversed(art_map):
        if pos < com_pos:
            art_num = anum
            is_adct = adct
            break

    # Source 1: bracket references (highest confidence)
    refs = re.findall(r'\[([^\]]{10,})\]', text)
    ref_meta = {}
    for ref in refs:
        rm = extract_from_ref(ref)
        for k, v in rm.items():
            if v and k not in ref_meta:
                ref_meta[k] = v

    # Source 2: inline links (medium confidence)
    link_meta = extract_from_links(raw)

    # Source 3: text patterns (safe patterns only)
    text_meta = extract_from_text(text)

    # Merge: ref > link > text
    final = {}
    for key in ['process_class', 'process_number', 'relator', 'redator',
                'julgamento_data', 'dje_data', 'tema_rg', 'turma',
                'merito_status', 'sumula_num', 'sumula_tipo', 'stf_incidente']:
        final[key] = ref_meta.get(key) or link_meta.get(key) or text_meta.get(key) or ''

    urls = link_meta.get('urls', [])
    labels = link_meta.get('link_labels', [])

    pk = f"{final['process_class']}_{final['process_number']}" if final['process_class'] and final['process_number'] else ''

    prefix = 'adct' if is_adct else 'cf'
    results.append({
        'com_id': com_id,
        'artigo': f'{prefix}-art-{art_num}',
        'process_class': final['process_class'],
        'process_number': final['process_number'],
        'process_key': pk,
        'relator': final['relator'],
        'redator': final['redator'],
        'julgamento_data': final['julgamento_data'],
        'dje_data': final['dje_data'],
        'turma': final['turma'],
        'tema_rg': final['tema_rg'],
        'sumula_num': final['sumula_num'],
        'sumula_tipo': final['sumula_tipo'],
        'merito_status': final['merito_status'],
        'stf_incidente': final['stf_incidente'],
        'url_principal': urls[0] if urls else '',
        'urls_todas': ' | '.join(urls),
        'link_labels': ' | '.join(labels),
        'referencia': '; '.join(refs)[:300],
        'texto_preview': text[:200],
        'fonte_relator': 'ref' if ref_meta.get('relator') else ('link' if link_meta.get('relator') else ('text' if text_meta.get('relator') else '')),
        'fonte_processo': 'ref' if ref_meta.get('process_class') else ('link' if link_meta.get('process_class') else ''),
    })

# ═══════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════

total = len(results)
with_rel = sum(1 for r in results if r['relator'])
with_pc = sum(1 for r in results if r['process_class'])
with_url = sum(1 for r in results if r['url_principal'])
with_julg = sum(1 for r in results if r['julgamento_data'])
with_tema = sum(1 for r in results if r['tema_rg'])
with_turma = sum(1 for r in results if r['turma'])
with_sumula = sum(1 for r in results if r['sumula_num'])

print(f"\n{'='*60}")
print(f"  METADADOS CONFIRMADOS")
print(f"{'='*60}")
print(f"  Total decisões: {total}")
print(f"  Com relator:    {with_rel} ({with_rel/total*100:.1f}%)")
print(f"  Com processo:   {with_pc} ({with_pc/total*100:.1f}%)")
print(f"  Com URL:        {with_url} ({with_url/total*100:.1f}%)")
print(f"  Com data julg:  {with_julg} ({with_julg/total*100:.1f}%)")
print(f"  Com turma:      {with_turma} ({with_turma/total*100:.1f}%)")
print(f"  Com tema RG:    {with_tema} ({with_tema/total*100:.1f}%)")
print(f"  Com súmula:     {with_sumula} ({with_sumula/total*100:.1f}%)")

# ═══════════════════════════════════════════
# SAVE TSV (Excel)
# ═══════════════════════════════════════════

out_path = Path(r"C:\projetos\icons\ingest\stf_metadata_confirmada.tsv")
fieldnames = ['com_id', 'artigo', 'process_class', 'process_number', 'process_key',
              'relator', 'redator', 'julgamento_data', 'dje_data', 'turma',
              'tema_rg', 'sumula_num', 'sumula_tipo', 'merito_status', 'stf_incidente',
              'url_principal', 'urls_todas', 'link_labels', 'referencia',
              'texto_preview', 'fonte_relator', 'fonte_processo']

with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
    w.writeheader()
    for r in results:
        w.writerow(r)

print(f"\n  Salvo: {out_path}")

# ═══════════════════════════════════════════
# UPDATE DATABASE
# ═══════════════════════════════════════════

print("\nAtualizando banco...")
con = sqlite3.connect(str(DB_PATH))

# Add new columns if missing
existing_cols = [r[1] for r in con.execute("PRAGMA table_info(decision_blocks_resolved)").fetchall()]
for col, ctype in [('turma', 'TEXT'), ('merito_status', 'TEXT'),
                    ('stf_incidente', 'TEXT'), ('url_principal', 'TEXT'),
                    ('sumula_tipo', 'TEXT')]:
    if col not in existing_cols:
        con.execute(f"ALTER TABLE decision_blocks_resolved ADD COLUMN {col} {ctype}")
        print(f"  Coluna adicionada: {col}")

updated = 0
for r in results:
    if not any([r['relator'], r['process_class'], r['julgamento_data'],
                r['turma'], r['tema_rg'], r['url_principal']]):
        continue

    pk = r['process_key'] or None
    con.execute("""
        UPDATE decision_blocks_resolved SET
            relator = COALESCE(NULLIF(?, ''), relator),
            redator = COALESCE(NULLIF(?, ''), redator),
            process_class = COALESCE(NULLIF(?, ''), process_class),
            process_number = COALESCE(NULLIF(?, ''), process_number),
            process_key = COALESCE(?, process_key),
            julgamento_data = COALESCE(NULLIF(?, ''), julgamento_data),
            dje_data = COALESCE(NULLIF(?, ''), dje_data),
            tema_rg = COALESCE(NULLIF(?, ''), tema_rg),
            sumula_num = COALESCE(NULLIF(?, ''), sumula_num),
            turma = COALESCE(NULLIF(?, ''), turma),
            merito_status = COALESCE(NULLIF(?, ''), merito_status),
            stf_incidente = COALESCE(NULLIF(?, ''), stf_incidente),
            url_principal = COALESCE(NULLIF(?, ''), url_principal),
            sumula_tipo = COALESCE(NULLIF(?, ''), sumula_tipo),
            metadata_text = COALESCE(NULLIF(?, ''), metadata_text),
            raw_signature = COALESCE(NULLIF(
                TRIM(COALESCE(NULLIF(?, ''), process_class) || ' ' ||
                     COALESCE(NULLIF(?, ''), process_number) || ' rel. ' ||
                     COALESCE(NULLIF(?, ''), relator)), 'rel.'),
                raw_signature)
        WHERE stf_com_id = ?
    """, (
        r['relator'], r['redator'], r['process_class'], r['process_number'], pk,
        r['julgamento_data'], r['dje_data'], r['tema_rg'], r['sumula_num'],
        r['turma'], r['merito_status'], r['stf_incidente'], r['url_principal'],
        r['sumula_tipo'], r['referencia'],
        r['process_class'], r['process_number'], r['relator'],
        r['com_id']
    ))
    updated += 1

con.commit()

# Final stats
stf_total = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved WHERE anchor_source='stf_import' AND decision_unit_type != 'marcador_editorial'").fetchone()[0]
for field, label in [('relator', 'relator'), ('process_class', 'processo'),
                     ('julgamento_data', 'data_julg'), ('turma', 'turma'),
                     ('tema_rg', 'tema'), ('url_principal', 'URL'),
                     ('sumula_num', 'súmula')]:
    n = con.execute(f"SELECT COUNT(*) FROM decision_blocks_resolved WHERE {field} IS NOT NULL AND {field} != '' AND anchor_source='stf_import' AND decision_unit_type != 'marcador_editorial'").fetchone()[0]
    print(f"  {label:12s}: {n}/{stf_total} ({n/stf_total*100:.1f}%)")

# Relatores
print(f"\nRelatores ({con.execute('SELECT COUNT(DISTINCT relator) FROM decision_blocks_resolved WHERE relator != \"\"').fetchone()[0]} únicos):")
for r in con.execute("SELECT relator, COUNT(*) FROM decision_blocks_resolved WHERE relator != '' GROUP BY relator ORDER BY COUNT(*) DESC LIMIT 20").fetchall():
    print(f"  {r[1]:5d} | {r[0]}")

con.close()
print("\nDone.")
