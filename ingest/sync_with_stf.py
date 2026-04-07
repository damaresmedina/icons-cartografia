"""
Sincroniza o banco com o STF online.
Usa o HTML do STF como ground truth para reancorar TODOS os blocos.
"""
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from difflib import SequenceMatcher

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

def clean(s):
    """Normaliza texto para comparação."""
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&[a-z]+;', ' ', s)
    s = re.sub(r'&#\d+;', ' ', s)
    s = re.sub(r'[^\w]', ' ', s.lower())
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# ═══════════════════════════════════════════
# 1. PARSE STF: extract every comment with its article number
# ═══════════════════════════════════════════

print("Parsing STF HTML...")

# Find article positions
art_positions = []
for m in re.finditer(r'id="(art\d+[a-z]*)"', html):
    pos = m.start()
    window = html[max(0, pos-500):pos+500]
    num_m = re.search(r'Art\.?\s*(\d+)', window)
    if num_m:
        art_positions.append((pos, int(num_m.group(1))))

# Find sub-devices (inc, par, ali) with positions
sub_positions = []
for m in re.finditer(r'id="(inc|par|ali)(\d+[a-z]*)"', html):
    sub_positions.append((m.start(), m.group(1), m.group(1) + m.group(2)))

# Extract all STF comments with: art_num, sub_device context, clean text
stf_comments = []
for i, (art_pos, art_num) in enumerate(art_positions):
    next_art_pos = art_positions[i + 1][0] if i + 1 < len(art_positions) else len(html)
    section = html[art_pos:next_art_pos]

    # Find sub-devices in this section (relative positions)
    subs_in_section = []
    for sp, stype, sid in sub_positions:
        if art_pos < sp < next_art_pos:
            subs_in_section.append((sp - art_pos, stype, sid))

    # Find comments in this section
    for cm in re.finditer(r'<div\s+class="com"\s+id="com(\d+)"[^>]*>(.*?)</div>', section, re.DOTALL):
        com_pos = cm.start()
        com_id = int(cm.group(1))
        raw_text = cm.group(2)
        cleaned = clean(raw_text)

        # Determine which sub-device this comment belongs to
        sub_device = None
        for sp, stype, sid in subs_in_section:
            if sp < com_pos:
                sub_device = (stype, sid)
            else:
                break

        stf_comments.append({
            'com_id': com_id,
            'art_num': art_num,
            'sub_device': sub_device,
            'text_clean': cleaned,
            'text_prefix_80': cleaned[:80],
            'text_prefix_50': cleaned[:50],
        })

print(f"  STF comments: {len(stf_comments)}")

# Build lookup indexes
stf_by_prefix80 = defaultdict(list)
stf_by_prefix50 = defaultdict(list)
for sc in stf_comments:
    if len(sc['text_prefix_80']) > 20:
        stf_by_prefix80[sc['text_prefix_80']].append(sc)
    if len(sc['text_prefix_50']) > 20:
        stf_by_prefix50[sc['text_prefix_50']].append(sc)

# ═══════════════════════════════════════════
# 2. LOAD OUR BLOCKS
# ═══════════════════════════════════════════

print("\nLoading our blocks...")
con = sqlite3.connect(str(DB_PATH))

our_blocks = con.execute("""
    SELECT block_id, anchor_slug, block_text, anchor_source,
           anchor_quality_recode, editorial_marker
    FROM decision_blocks_resolved
    ORDER BY block_id
""").fetchall()

print(f"  Our blocks: {len(our_blocks)}")

# ═══════════════════════════════════════════
# 3. MATCH EACH OUR BLOCK TO STF
# ═══════════════════════════════════════════

print("\nMatching...")

matched = []
unmatched = []
already_correct = 0
fixed = 0

for r in our_blocks:
    bid, slug, text, src, qr, ed = r
    if not text or not slug:
        unmatched.append(bid)
        continue

    our_clean = clean(text)
    our_p80 = our_clean[:80]
    our_p50 = our_clean[:50]

    # Extract our article number
    art_m = re.match(r'cf-1988-art-(\d+)', slug)
    if not art_m:
        # ADCT or other
        unmatched.append(bid)
        continue
    our_art = int(art_m.group(1))

    # Try match by 80-char prefix
    stf_match = stf_by_prefix80.get(our_p80)
    if not stf_match and len(our_p50) > 20:
        stf_match = stf_by_prefix50.get(our_p50)

    if not stf_match:
        unmatched.append(bid)
        continue

    # Take the first match (most are unique)
    stf_art = stf_match[0]['art_num']

    if stf_art == our_art:
        already_correct += 1
        matched.append(bid)
        continue

    # Need to fix: change article in slug
    sub_device = re.sub(r'^cf-1988-art-\d+', '', slug)
    new_slug = f"cf-1988-art-{stf_art}{sub_device}"

    con.execute(
        "UPDATE decision_blocks_resolved SET anchor_slug = ? WHERE block_id = ?",
        (new_slug, bid)
    )
    con.execute(
        "UPDATE block_anchors SET anchor_slug = ? WHERE block_id = ? AND anchor_role = 'primary'",
        (new_slug, bid)
    )

    fixed += 1
    matched.append(bid)

con.commit()

print(f"\n  Already correct: {already_correct}")
print(f"  Fixed: {fixed}")
print(f"  Unmatched (no STF equivalent): {len(unmatched)}")
print(f"  Total matched: {len(matched)}")

# ═══════════════════════════════════════════
# 4. FINAL COMPARISON
# ═══════════════════════════════════════════

# Recount
stf_by_art = defaultdict(int)
for sc in stf_comments:
    stf_by_art[sc['art_num']] += 1

our_by_art = defaultdict(int)
for r in con.execute("""
    SELECT anchor_slug, COUNT(*) FROM decision_blocks_resolved
    WHERE anchor_slug IS NOT NULL AND anchor_slug != ''
    GROUP BY anchor_slug
""").fetchall():
    m = re.match(r'cf-1988-art-(\d+)', r[0])
    if m:
        our_by_art[int(m.group(1))] += r[1]

all_arts = sorted(set(list(stf_by_art.keys()) + list(our_by_art.keys())))

ok = 0
diverge = 0
diverge_list = []
perfect = 0

for art in all_arts:
    s = stf_by_art.get(art, 0)
    o = our_by_art.get(art, 0)
    d = o - s
    pct = (d / s * 100) if s > 0 else (100 if o > 0 else 0)

    if d == 0:
        perfect += 1
        ok += 1
    elif abs(pct) <= 20 or abs(d) <= 2:
        ok += 1
    else:
        diverge += 1
        diverge_list.append((art, s, o, d))

total_stf = sum(stf_by_art.values())
total_ours = sum(our_by_art.values())

print(f"\n{'='*60}")
print(f"  RESULTADO FINAL")
print(f"{'='*60}")
print(f"  Artigos: {len(all_arts)}")
print(f"  Perfect match: {perfect}")
print(f"  OK (diff <= 20%): {ok}")
print(f"  Diverge: {diverge}")
print(f"  STF total: {total_stf}")
print(f"  Nosso total: {total_ours}")
print(f"  Diff global: {total_ours - total_stf:+d}")

if diverge_list:
    print(f"\n  Artigos divergentes (top 20):")
    for art, s, o, d in sorted(diverge_list, key=lambda x: -abs(x[3]))[:20]:
        print(f"    Art {art:>4d} | STF={s:>4d} Nosso={o:>4d} diff={d:>+5d}")

# Count how many STF comments we're missing entirely
stf_matched_arts = set()
for sc in stf_comments:
    stf_matched_arts.add(sc['art_num'])

missing_from_stf = total_stf - (already_correct + fixed)
print(f"\n  Blocos STF sem match no nosso banco: ~{missing_from_stf}")

con.close()
print("\nDone.")
