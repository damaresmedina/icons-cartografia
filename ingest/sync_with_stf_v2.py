"""
Sync v2: Match agressivo removendo editorial prefix do texto STF.
"""
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

EDITORIAL_PREFIXES = [
    'controle concentrado de constitucionalidade',
    'controle de concentrado de constitucionalidade',
    'repercussão geral', 'repercussao geral',
    'súmula vinculante', 'sumula vinculante',
    'súmula', 'sumula',
    'julgados correlatos', 'julgado correlato',
    'preâmbulo', 'preambulo',
]

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&[a-z]+;', ' ', s)
    s = re.sub(r'&#\d+;', ' ', s)
    # Normalize unicode chars
    s = s.replace('\u00e7', 'c').replace('\u00e3', 'a').replace('\u00f5', 'o')
    s = s.replace('\u00e9', 'e').replace('\u00ed', 'i').replace('\u00f3', 'o')
    s = s.replace('\u00fa', 'u').replace('\u00e1', 'a').replace('\u00ea', 'e')
    s = s.replace('\u00f4', 'o').replace('\u00e0', 'a').replace('\u00e2', 'a')
    s = s.replace('\u00fc', 'u').replace('\u00f1', 'n')
    s = re.sub(r'[^\w]', ' ', s.lower())
    s = re.sub(r'\s+', ' ', s).strip()
    # Remove editorial prefixes
    for prefix in EDITORIAL_PREFIXES:
        p_clean = re.sub(r'[^\w]', ' ', prefix.lower())
        p_clean = re.sub(r'\s+', ' ', p_clean).strip()
        if s.startswith(p_clean):
            s = s[len(p_clean):].strip()
    return s

# ═══════════════════════════════════════════
# 1. PARSE STF COMMENTS
# ═══════════════════════════════════════════

print("Parsing STF...")
art_positions = []
for m in re.finditer(r'id="(art\d+[a-z]*)"', html):
    pos = m.start()
    window = html[max(0, pos-500):pos+500]
    num_m = re.search(r'Art\.?\s*(\d+)', window)
    if num_m:
        art_positions.append((pos, int(num_m.group(1))))

stf_comments = []
for i, (art_pos, art_num) in enumerate(art_positions):
    next_pos = art_positions[i + 1][0] if i + 1 < len(art_positions) else len(html)
    section = html[art_pos:next_pos]
    for cm in re.finditer(r'<div\s+class="com"\s+id="com(\d+)"[^>]*>(.*?)</div>', section, re.DOTALL):
        raw = cm.group(2)
        cleaned = clean(raw)
        stf_comments.append({
            'art_num': art_num,
            'text_clean': cleaned,
        })

print(f"  STF comments: {len(stf_comments)}")

# Build multiple lookup indexes with different prefix lengths
stf_lookup = {}
for sc in stf_comments:
    for length in [100, 80, 60, 40]:
        prefix = sc['text_clean'][:length]
        if len(prefix) >= length:
            key = (length, prefix)
            if key not in stf_lookup:
                stf_lookup[key] = sc['art_num']

print(f"  Lookup entries: {len(stf_lookup)}")

# ═══════════════════════════════════════════
# 2. MATCH AND FIX
# ═══════════════════════════════════════════

print("\nMatching...")
con = sqlite3.connect(str(DB_PATH))

rows = con.execute("""
    SELECT block_id, anchor_slug, block_text
    FROM decision_blocks_resolved
    ORDER BY block_id
""").fetchall()

correct = 0
fixed = 0
unmatched = 0

for bid, slug, text in rows:
    if not text or not slug:
        unmatched += 1
        continue

    art_m = re.match(r'cf-1988-art-(\d+)', slug)
    if not art_m:
        unmatched += 1
        continue
    our_art = int(art_m.group(1))

    our_clean = clean(text)

    # Try matching with decreasing prefix lengths
    stf_art = None
    for length in [100, 80, 60, 40]:
        prefix = our_clean[:length]
        if len(prefix) >= length:
            stf_art = stf_lookup.get((length, prefix))
            if stf_art is not None:
                break

    if stf_art is None:
        unmatched += 1
        continue

    if stf_art == our_art:
        correct += 1
        continue

    # Fix
    sub = re.sub(r'^cf-1988-art-\d+', '', slug)
    new_slug = f"cf-1988-art-{stf_art}{sub}"
    con.execute("UPDATE decision_blocks_resolved SET anchor_slug = ? WHERE block_id = ?", (new_slug, bid))
    con.execute("UPDATE block_anchors SET anchor_slug = ? WHERE block_id = ? AND anchor_role = 'primary'", (new_slug, bid))
    fixed += 1

con.commit()
print(f"  Correct: {correct}")
print(f"  Fixed: {fixed}")
print(f"  Unmatched: {unmatched}")

# ═══════════════════════════════════════════
# 3. FINAL VERIFICATION
# ═══════════════════════════════════════════

stf_by_art = defaultdict(int)
for sc in stf_comments:
    stf_by_art[sc['art_num']] += 1

our_by_art = defaultdict(int)
for r in con.execute("SELECT anchor_slug, COUNT(*) FROM decision_blocks_resolved WHERE anchor_slug IS NOT NULL GROUP BY anchor_slug").fetchall():
    m = re.match(r'cf-1988-art-(\d+)', r[0])
    if m:
        our_by_art[int(m.group(1))] += r[1]

all_arts = sorted(set(list(stf_by_art.keys()) + list(our_by_art.keys())))
ok = diverge = perfect = 0
diverge_list = []

for art in all_arts:
    s = stf_by_art.get(art, 0)
    o = our_by_art.get(art, 0)
    d = o - s
    if d == 0:
        perfect += 1
        ok += 1
    elif abs(d) <= 2 or (s > 0 and abs(d / s) <= 0.15):
        ok += 1
    else:
        diverge += 1
        diverge_list.append((art, s, o, d))

print(f"\n{'='*60}")
print(f"  RESULTADO FINAL")
print(f"{'='*60}")
print(f"  Perfect: {perfect}")
print(f"  OK: {ok}")
print(f"  Diverge: {diverge}")
print(f"  STF: {sum(stf_by_art.values())}  Nosso: {sum(our_by_art.values())}  Diff: {sum(our_by_art.values())-sum(stf_by_art.values()):+d}")

if diverge_list:
    print(f"\n  Top divergentes:")
    for art, s, o, d in sorted(diverge_list, key=lambda x: -abs(x[3]))[:15]:
        print(f"    Art {art:>4d} | STF={s:>4d} Nosso={o:>4d} diff={d:>+5d}")

con.close()
print("\nDone.")
