"""
Parse STF HTML v2 — extrai hierarquia completa artigo→dispositivo→editorial→bloco
para cruzar com nosso banco.
"""
import re
import json
import sqlite3
from collections import defaultdict, Counter
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")
OUT_PATH = Path(r"C:\projetos\icons\ingest\stf_vs_banco.json")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

# ═══════════════════════════════════════════
# 1. FIND ALL POSITIONED ELEMENTS
# ═══════════════════════════════════════════

# Devices: art, inc, ali, par
devices = []
for m in re.finditer(r'id="(art|inc|par|ali)(\d+[a-z]*)"', html):
    devices.append((m.start(), m.group(1), m.group(1) + m.group(2)))

# Comments: com
comments = []
for m in re.finditer(r'id="com(\d+)"', html):
    comments.append((m.start(), int(m.group(1))))

print(f"Devices: {len(devices)}")
print(f"Comments: {len(comments)}")

# ═══════════════════════════════════════════
# 2. BUILD ARTICLE SECTIONS
# ═══════════════════════════════════════════

# Find article boundaries
art_positions = [(pos, did) for pos, dtype, did in devices if dtype == 'art']

# For each article, extract its section of HTML
articles = []
for i, (pos, art_id) in enumerate(art_positions):
    next_pos = art_positions[i + 1][0] if i + 1 < len(art_positions) else len(html)

    # Get label
    chunk = html[pos:pos + 500]
    label_m = re.search(r'>([^<]{3,200})</', chunk)
    label = re.sub(r'&[^;]+;', ' ', label_m.group(1)).strip()[:120] if label_m else ''
    art_num_m = re.match(r'Art\.?\s*(\d+)', label)
    art_num = int(art_num_m.group(1)) if art_num_m else None

    # Sub-devices in this article section
    subs = [(p, dt, did) for p, dt, did in devices if pos < p < next_pos and dt != 'art']

    # Comments in this article section
    art_comments = [(p, cid) for p, cid in comments if pos < p < next_pos]

    # Map each comment to its nearest preceding sub-device (or caput if none)
    sub_positions = sorted([(p, did) for p, _, did in subs])

    comment_map = defaultdict(list)  # device_id -> [com_ids]
    for cpos, cid in art_comments:
        assigned = 'caput'
        for spos, sid in sub_positions:
            if spos < cpos:
                assigned = sid
            else:
                break
        comment_map[assigned].append(cid)

    # Build sub-device list with labels
    sub_list = []
    for _, dt, did in subs:
        # Get label
        idx = html.find(f'id="{did}"')
        if idx >= 0:
            sub_chunk = html[idx:idx + 400]
            sub_label_m = re.search(r'>([^<]{2,200})</', sub_chunk)
            sub_label = re.sub(r'&[^;]+;', ' ', sub_label_m.group(1)).strip()[:100] if sub_label_m else ''
        else:
            sub_label = ''

        sub_list.append({
            'type': dt,
            'id': did,
            'label': sub_label,
            'comments': len(comment_map.get(did, [])),
        })

    articles.append({
        'art_id': art_id,
        'art_num': art_num,
        'label': label,
        'caput_comments': len(comment_map.get('caput', [])),
        'sub_devices': sub_list,
        'total_comments': len(art_comments),
        'sub_device_counts': {
            'inc': sum(1 for s in sub_list if s['type'] == 'inc'),
            'par': sum(1 for s in sub_list if s['type'] == 'par'),
            'ali': sum(1 for s in sub_list if s['type'] == 'ali'),
        },
    })

print(f"Articles parsed: {len(articles)}")
total_coms = sum(a['total_comments'] for a in articles)
print(f"Total comments mapped: {total_coms}")

# ═══════════════════════════════════════════
# 3. LOAD OUR BANCO AND COMPARE
# ═══════════════════════════════════════════

con = sqlite3.connect(str(DB_PATH))

# Our blocks per slug
our_by_slug = defaultdict(int)
for r in con.execute("""
    SELECT anchor_slug, COUNT(*) FROM decision_blocks_resolved
    WHERE anchor_slug IS NOT NULL AND anchor_slug != ''
    GROUP BY anchor_slug
""").fetchall():
    our_by_slug[r[0]] = r[1]

# Our blocks per article number
our_by_art = defaultdict(int)
for slug, n in our_by_slug.items():
    m = re.match(r'cf-1988-art-(\d+)', slug)
    if m:
        our_by_art[int(m.group(1))] += n

# Our sub-devices per article
our_subs_by_art = defaultdict(lambda: {'inc': 0, 'par': 0, 'ali': 0, 'total_blocks': 0})
for slug, n in our_by_slug.items():
    m = re.match(r'cf-1988-art-(\d+)', slug)
    if not m:
        continue
    art = int(m.group(1))
    our_subs_by_art[art]['total_blocks'] += n
    if '-inc-' in slug:
        our_subs_by_art[art]['inc'] += 1
    if '-par-' in slug:
        our_subs_by_art[art]['par'] += 1
    if '-ali-' in slug:
        our_subs_by_art[art]['ali'] += 1

con.close()

# ═══════════════════════════════════════════
# 4. CROSS-REFERENCE
# ═══════════════════════════════════════════

print(f"\n{'='*80}")
print(f"  CRUZAMENTO STF ONLINE vs BANCO")
print(f"{'='*80}")

comparison = []
for art in articles:
    if art['art_num'] is None:
        continue
    n = art['art_num']
    stf_total = art['total_comments']
    our_total = our_by_art.get(n, 0)
    diff = our_total - stf_total
    pct_diff = (diff / stf_total * 100) if stf_total > 0 else (100 if our_total > 0 else 0)

    stf_subs = art['sub_device_counts']
    our_subs = our_subs_by_art.get(n, {'inc': 0, 'par': 0, 'ali': 0})

    entry = {
        'art_num': n,
        'stf_total': stf_total,
        'our_total': our_total,
        'diff': diff,
        'pct_diff': round(pct_diff, 1),
        'stf_caput': art['caput_comments'],
        'stf_inc': stf_subs['inc'],
        'stf_par': stf_subs['par'],
        'stf_ali': stf_subs['ali'],
        'our_inc': our_subs['inc'],
        'our_par': our_subs['par'],
        'our_ali': our_subs['ali'],
        'status': 'OK' if abs(pct_diff) <= 30 or abs(diff) <= 3 else ('DEFICIT' if diff < 0 else 'EXCESSO'),
    }
    comparison.append(entry)

# Print divergent articles
print(f"\n{'Art':>5s} | {'STF':>5s} | {'Nosso':>5s} | {'Diff':>6s} | {'%':>7s} | {'STF i/p/a':>10s} | {'N i/p/a':>10s} | Status")
print("-" * 85)

divergent = [c for c in comparison if c['status'] != 'OK']
for c in sorted(divergent, key=lambda x: abs(x['diff']), reverse=True):
    print(
        f"{c['art_num']:>5d} | {c['stf_total']:>5d} | {c['our_total']:>5d} | {c['diff']:>+6d} | "
        f"{c['pct_diff']:>+6.1f}% | {c['stf_inc']:>2d}/{c['stf_par']:>2d}/{c['stf_ali']:>2d}     | "
        f"{c['our_inc']:>2d}/{c['our_par']:>2d}/{c['our_ali']:>2d}     | {c['status']}"
    )

# Summary
ok = sum(1 for c in comparison if c['status'] == 'OK')
deficit = sum(1 for c in comparison if c['status'] == 'DEFICIT')
excesso = sum(1 for c in comparison if c['status'] == 'EXCESSO')

total_stf = sum(c['stf_total'] for c in comparison)
total_ours = sum(c['our_total'] for c in comparison)

print(f"\n  RESUMO")
print(f"  Artigos comparados: {len(comparison)}")
print(f"  OK: {ok}  |  Deficit: {deficit}  |  Excesso: {excesso}")
print(f"  Total STF: {total_stf}  |  Total nosso: {total_ours}  |  Diff global: {total_ours - total_stf:+d}")

# Save
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump({'comparison': comparison, 'articles_detail': articles}, f, ensure_ascii=False, indent=2)
print(f"\n  Salvo: {OUT_PATH}")
