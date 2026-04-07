"""
Sync final: normaliza para ASCII puro antes de comparar.
"""
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

EDITORIAL_STRIP = re.compile(
    r'^(controle\s+(de\s+)?concentrado\s+de\s+constitucionalidade|'
    r'repercuss.o\s+geral|s.mula\s+vinculante|s.mula|'
    r'julgados?\s+correlatos?|pre.mbulo)\s*',
    re.IGNORECASE
)

def to_key(s):
    """Full normalization: strip HTML, entities, accents, punctuation."""
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&[a-z]+;', ' ', s)
    s = re.sub(r'&#\d+;', ' ', s)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = EDITORIAL_STRIP.sub('', s)
    s = re.sub(r'[^a-z0-9]', '', s)  # only alphanumeric
    return s[:80]

# Parse STF
print("Parsing STF...")
art_positions = []
for m in re.finditer(r'id="(art\d+[a-z]*)"', html):
    pos = m.start()
    window = html[max(0, pos-500):pos+500]
    num_m = re.search(r'Art\.?\s*(\d+)', window)
    if num_m:
        art_positions.append((pos, int(num_m.group(1))))

stf_lookup = {}  # key -> art_num
stf_count_by_art = defaultdict(int)
for i, (art_pos, art_num) in enumerate(art_positions):
    next_pos = art_positions[i + 1][0] if i + 1 < len(art_positions) else len(html)
    section = html[art_pos:next_pos]
    for cm in re.finditer(r'<div\s+class="com"\s+id="com\d+"[^>]*>(.*?)</div>', section, re.DOTALL):
        stf_count_by_art[art_num] += 1
        key = to_key(cm.group(1))
        if key and len(key) >= 30:
            if key not in stf_lookup:
                stf_lookup[key] = art_num

print(f"  STF comments: {sum(stf_count_by_art.values())}")
print(f"  Lookup keys: {len(stf_lookup)}")

# Match our blocks
print("\nMatching...")
con = sqlite3.connect(str(DB_PATH))
rows = con.execute("SELECT block_id, anchor_slug, block_text FROM decision_blocks_resolved ORDER BY block_id").fetchall()

correct = fixed = unmatched = 0
for bid, slug, text in rows:
    if not text or not slug:
        unmatched += 1
        continue
    art_m = re.match(r'cf-1988-art-(\d+)', slug)
    if not art_m:
        unmatched += 1
        continue
    our_art = int(art_m.group(1))

    key = to_key(text)
    if not key or len(key) < 30:
        unmatched += 1
        continue

    stf_art = stf_lookup.get(key)

    # Try shorter keys if no match
    if stf_art is None:
        short = key[:60]
        for sk, sa in stf_lookup.items():
            if sk[:60] == short:
                stf_art = sa
                break

    if stf_art is None:
        # Even shorter
        short = key[:40]
        for sk, sa in stf_lookup.items():
            if sk[:40] == short:
                stf_art = sa
                break

    if stf_art is None:
        unmatched += 1
        continue

    if stf_art == our_art:
        correct += 1
        continue

    sub = re.sub(r'^cf-1988-art-\d+', '', slug)
    new_slug = f"cf-1988-art-{stf_art}{sub}"
    con.execute("UPDATE decision_blocks_resolved SET anchor_slug = ? WHERE block_id = ?", (new_slug, bid))
    con.execute("UPDATE block_anchors SET anchor_slug = ? WHERE block_id = ? AND anchor_role = 'primary'", (new_slug, bid))
    fixed += 1

con.commit()
print(f"  Correct: {correct}")
print(f"  Fixed: {fixed}")
print(f"  Unmatched: {unmatched}")

# Final comparison
our_by_art = defaultdict(int)
for r in con.execute("SELECT anchor_slug, COUNT(*) FROM decision_blocks_resolved WHERE anchor_slug IS NOT NULL GROUP BY anchor_slug").fetchall():
    m = re.match(r'cf-1988-art-(\d+)', r[0])
    if m:
        our_by_art[int(m.group(1))] += r[1]

all_arts = sorted(set(list(stf_count_by_art.keys()) + list(our_by_art.keys())))
perfect = ok = diverge = 0
diverge_list = []

for art in all_arts:
    s = stf_count_by_art.get(art, 0)
    o = our_by_art.get(art, 0)
    d = o - s
    if d == 0:
        perfect += 1; ok += 1
    elif abs(d) <= 2 or (s > 0 and abs(d / s) <= 0.10):
        ok += 1
    else:
        diverge += 1
        diverge_list.append((art, s, o, d))

total_stf = sum(stf_count_by_art.values())
total_ours = sum(our_by_art.values())

print(f"\n{'='*60}")
print(f"  RESULTADO FINAL")
print(f"{'='*60}")
print(f"  Perfect: {perfect}/{len(all_arts)}")
print(f"  OK (diff<=10%): {ok}")
print(f"  Diverge: {diverge}")
print(f"  STF: {total_stf}  Nosso: {total_ours}  Diff: {total_ours-total_stf:+d}")

if diverge_list:
    print(f"\n  Divergentes:")
    for art, s, o, d in sorted(diverge_list, key=lambda x: -abs(x[3])):
        print(f"    Art {art:>4d} | STF={s:>4d} Nosso={o:>4d} diff={d:>+5d}")

con.close()
print("\nDone.")
