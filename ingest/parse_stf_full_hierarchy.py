"""
Parse STF HTML extraindo hierarquia completa:
Art -> §/inc/ali -> editorial -> blocos de comentário
Gera JSON de referência para cruzar com nosso banco.
"""
import re
import json
from collections import defaultdict
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
OUT_PATH = Path(r"C:\projetos\icons\ingest\stf_hierarchy.json")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

# ═══════════════════════════════════════════
# 1. FIND ALL STRUCTURAL ANCHORS IN THE HTML
# ═══════════════════════════════════════════

# Article anchors: id="artN"
# Sub-device anchors: id="incN", id="parN", id="aliN" etc.
# Comment blocks: class="com" id="comN"
# Editorial markers: class="com-titulo" containing editorial name

def normalize_editorial(text):
    t = text.lower().strip()
    if 'súmula vinculante' in t or 'sumula vinculante' in t:
        return 'sumula_vinculante'
    if 'súmula' in t or 'sumula' in t:
        return 'sumula'
    if 'controle concentrado' in t:
        return 'controle_concentrado'
    if 'repercussão geral' in t or 'repercussao geral' in t:
        return 'repercussao_geral'
    if 'julgado' in t and 'correlato' in t:
        return 'julgados_correlatos'
    return t.replace(' ', '_')

# Find all anchors with their positions
anchors = []
for m in re.finditer(r'id="(art|inc|par|ali|item)(\d+[a-z]*)"', html, re.IGNORECASE):
    anchors.append({
        'pos': m.start(),
        'type': m.group(1).lower(),
        'id': m.group(1).lower() + m.group(2),
        'full_id': m.group(0),
    })

# Find all editorial markers
editorials = []
for m in re.finditer(r'class="com-titulo"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE):
    text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    editorials.append({
        'pos': m.start(),
        'text': text,
        'normalized': normalize_editorial(text) if text else '',
    })

# Find all comment blocks
comments = []
for m in re.finditer(r'<div\s+class="com"\s+id="com(\d+)"[^>]*>(.*?)</div>\s*(?=<div|$)', html, re.DOTALL | re.IGNORECASE):
    text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    comments.append({
        'pos': m.start(),
        'com_id': int(m.group(1)),
        'text_preview': text[:150],
        'text_len': len(text),
    })

print(f"Anchors: {len(anchors)}")
print(f"Editorials: {len(editorials)}")
print(f"Comments: {len(comments)}")


# Re-process editorials (already normalized above)
pass


# ═══════════════════════════════════════════
# 2. EXTRACT DEVICE LABELS (Art text, § text, etc.)
# ═══════════════════════════════════════════

device_labels = {}
for anchor in anchors:
    # Get text near this anchor
    start = anchor['pos']
    chunk = html[start:start + 500]
    # Find the label text
    label_match = re.search(r'>([^<]{3,200})</', chunk)
    if label_match:
        label = re.sub(r'&[^;]+;', '', label_match.group(1)).strip()
        device_labels[anchor['id']] = label[:120]


# ═══════════════════════════════════════════
# 3. BUILD HIERARCHY: assign comments to devices + editorials
# ═══════════════════════════════════════════

# Merge all positioned elements and sort
elements = []
for a in anchors:
    elements.append({'pos': a['pos'], 'kind': 'device', 'data': a})
for e in editorials:
    elements.append({'pos': e['pos'], 'kind': 'editorial', 'data': e})
for c in comments:
    elements.append({'pos': c['pos'], 'kind': 'comment', 'data': c})

elements.sort(key=lambda x: x['pos'])

# Walk through elements, maintaining current device stack and editorial
current_art = None
current_sub = None  # par/inc/ali within current art
current_editorial = None

# Result structure
hierarchy = []  # list of articles
current_art_entry = None

for el in elements:
    if el['kind'] == 'device':
        dev = el['data']
        if dev['type'] == 'art':
            # New article
            label = device_labels.get(dev['id'], '')
            art_match = re.match(r'Art\.?\s*(\d+)', label)
            art_num = int(art_match.group(1)) if art_match else None

            current_art_entry = {
                'art_id': dev['id'],
                'art_num': art_num,
                'label': label,
                'sub_devices': [],
                'direct_comments': [],  # comments directly under the article (caput)
                'current_sub': None,
            }
            hierarchy.append(current_art_entry)
            current_sub = None
            current_editorial = None

        elif dev['type'] in ('par', 'inc', 'ali', 'item'):
            if current_art_entry:
                label = device_labels.get(dev['id'], '')
                sub = {
                    'type': dev['type'],
                    'id': dev['id'],
                    'label': label,
                    'comments': [],
                }
                current_art_entry['sub_devices'].append(sub)
                current_sub = sub
                current_editorial = None

    elif el['kind'] == 'editorial':
        current_editorial = el['data']['normalized']

    elif el['kind'] == 'comment':
        com = el['data']
        com_entry = {
            'com_id': com['com_id'],
            'editorial': current_editorial or '',
            'text_preview': com['text_preview'],
            'text_len': com['text_len'],
        }

        if current_art_entry:
            if current_sub:
                current_sub['comments'].append(com_entry)
            else:
                current_art_entry['direct_comments'].append(com_entry)


# ═══════════════════════════════════════════
# 4. SUMMARY
# ═══════════════════════════════════════════

print(f"\n{'='*60}")
print(f"  STF HIERARCHY PARSED")
print(f"{'='*60}")
print(f"  Artigos: {len(hierarchy)}")

total_comments = 0
total_sub_devices = 0
arts_with_subs = 0

for art in hierarchy:
    n_direct = len(art['direct_comments'])
    n_sub_comments = sum(len(s['comments']) for s in art['sub_devices'])
    total_comments += n_direct + n_sub_comments
    total_sub_devices += len(art['sub_devices'])
    if art['sub_devices']:
        arts_with_subs += 1

print(f"  Sub-devices (par/inc/ali): {total_sub_devices}")
print(f"  Artigos com sub-devices: {arts_with_subs}")
print(f"  Total comments: {total_comments}")

# Editorial distribution
ed_counts = defaultdict(int)
for art in hierarchy:
    for c in art['direct_comments']:
        ed_counts[c['editorial']] += 1
    for sub in art['sub_devices']:
        for c in sub['comments']:
            ed_counts[c['editorial']] += 1

print(f"\n  Por editorial:")
for ed, n in sorted(ed_counts.items(), key=lambda x: -x[1]):
    print(f"    {ed or '(sem)':30s} {n:5d}")

# Show Art. 5 as example
print(f"\n  === Art. 5 (exemplo) ===")
for art in hierarchy:
    if art['art_num'] == 5:
        print(f"  Direct comments (caput): {len(art['direct_comments'])}")
        for sub in art['sub_devices'][:10]:
            n_com = len(sub['comments'])
            eds = defaultdict(int)
            for c in sub['comments']:
                eds[c['editorial']] += 1
            ed_str = ', '.join(f"{k}:{v}" for k, v in eds.items())
            print(f"    {sub['type']:4s} {sub['id']:15s} | {n_com:3d} comments | {ed_str}")
        if len(art['sub_devices']) > 10:
            print(f"    ... +{len(art['sub_devices'])-10} sub-devices")
        break

# Save
# Clean up for JSON serialization
for art in hierarchy:
    if 'current_sub' in art:
        del art['current_sub']

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(hierarchy, f, ensure_ascii=False, indent=2)

print(f"\n  Salvo: {OUT_PATH}")
print(f"  Tamanho: {OUT_PATH.stat().st_size / 1024:.0f} KB")
