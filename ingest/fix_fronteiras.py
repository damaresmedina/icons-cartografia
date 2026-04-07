"""
Fix fronteiras: usa STF online como ground truth para corrigir blocos
que vazaram entre artigos vizinhos.

Estratégia:
1. Para cada par (artigo_deficit, artigo_excesso vizinho), identificar blocos
   que estão no artigo errado
2. Usar o texto dos blocos para cruzar com o HTML do STF e confirmar o artigo correto
3. Atualizar anchor_slug no banco
"""
import re
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
DB_PATH = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

# ═══════════════════════════════════════════
# 1. BUILD STF ARTICLE SECTIONS WITH TEXT
# ═══════════════════════════════════════════

# Find art positions and map to art numbers
art_positions = []
for m in re.finditer(r'id="(art\d+[a-z]*)"', html):
    pos = m.start()
    art_id = m.group(1)
    # Find Art. N in nearby text
    window = html[max(0, pos-500):pos+500]
    num_m = re.search(r'Art\.?\s*(\d+)', window)
    if num_m:
        art_positions.append((pos, int(num_m.group(1)), art_id))

# Build article text sections (strip HTML, keep text for matching)
def strip_html(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&[a-z]+;', ' ', s)
    s = re.sub(r'&#\d+;', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

# For each article, extract all comment texts
stf_article_texts = {}  # art_num -> list of comment text previews
for i, (pos, art_num, art_id) in enumerate(art_positions):
    next_pos = art_positions[i + 1][0] if i + 1 < len(art_positions) else len(html)
    section = html[pos:next_pos]

    # Extract each com block's text
    texts = []
    for cm in re.finditer(r'<div\s+class="com"\s+id="com\d+"[^>]*>(.*?)</div>', section, re.DOTALL):
        t = strip_html(cm.group(1))[:200]
        texts.append(t)

    if art_num not in stf_article_texts:
        stf_article_texts[art_num] = texts
    else:
        stf_article_texts[art_num].extend(texts)

print(f"STF articles with texts: {len(stf_article_texts)}")
total_stf_texts = sum(len(v) for v in stf_article_texts.values())
print(f"Total STF comment texts: {total_stf_texts}")

# Build lookup: text_prefix -> art_num (for matching)
stf_text_to_art = {}
for art_num, texts in stf_article_texts.items():
    for t in texts:
        key = t[:100].strip().lower()
        if key and len(key) > 20:
            stf_text_to_art[key] = art_num

print(f"Text lookup entries: {len(stf_text_to_art)}")

# ═══════════════════════════════════════════
# 2. LOAD OUR BLOCKS AND FIND MISMATCHES
# ═══════════════════════════════════════════

con = sqlite3.connect(str(DB_PATH))

rows = con.execute("""
    SELECT block_id, anchor_slug, block_text, anchor_source,
           anchor_quality_recode, editorial_marker
    FROM decision_blocks_resolved
    ORDER BY block_id
""").fetchall()

print(f"\nOur blocks: {len(rows)}")

# For each block, try to match its text against STF lookup
fixes = []
no_match = 0
already_correct = 0
matched_different = 0

for r in rows:
    bid, slug, text, src, qr, ed = r
    if not text or not slug:
        continue

    # Extract our article number
    m = re.match(r'cf-1988-art-(\d+)', slug)
    if not m:
        continue
    our_art = int(m.group(1))

    # Clean our text for matching
    our_key = strip_html(text)[:100].strip().lower()
    if len(our_key) < 20:
        continue

    # Look up in STF
    stf_art = stf_text_to_art.get(our_key)

    if stf_art is None:
        # Try shorter prefix
        our_key_short = our_key[:60]
        for stf_key, stf_num in stf_text_to_art.items():
            if stf_key.startswith(our_key_short):
                stf_art = stf_num
                break

    if stf_art is None:
        no_match += 1
        continue

    if stf_art == our_art:
        already_correct += 1
        continue

    # Mismatch found!
    matched_different += 1

    # Build corrected slug: replace art-N with art-STF_N, keep sub-device
    # Only change the article number, preserve inc/par/ali suffix
    sub_device = re.sub(r'^cf-1988-art-\d+', '', slug)
    new_slug = f"cf-1988-art-{stf_art}{sub_device}"

    fixes.append({
        'block_id': bid,
        'old_slug': slug,
        'new_slug': new_slug,
        'old_art': our_art,
        'new_art': stf_art,
        'source': src,
        'quality': qr,
        'text_preview': text[:60] if text else '',
    })

print(f"\nResults:")
print(f"  Already correct: {already_correct}")
print(f"  No match in STF: {no_match}")
print(f"  Need fix (different art): {matched_different}")

# ═══════════════════════════════════════════
# 3. ANALYZE FIXES
# ═══════════════════════════════════════════

# Group by (old_art -> new_art)
from collections import Counter
fix_patterns = Counter((f['old_art'], f['new_art']) for f in fixes)
print(f"\n{'Old Art':>8s} -> {'New Art':>8s} : {'Count':>5s}")
print("-" * 35)
for (old, new), n in fix_patterns.most_common(30):
    print(f"  Art {old:>4d} -> Art {new:>4d} : {n:>5d}")

# ═══════════════════════════════════════════
# 4. APPLY FIXES
# ═══════════════════════════════════════════

print(f"\n{'='*60}")
print(f"  APPLYING {len(fixes)} FIXES")
print(f"{'='*60}")

# Update anchor_slug in decision_blocks_resolved
for f in fixes:
    con.execute("""
        UPDATE decision_blocks_resolved
        SET anchor_slug = ?
        WHERE block_id = ?
    """, (f['new_slug'], f['block_id']))

# Also update block_anchors primary
for f in fixes:
    con.execute("""
        UPDATE block_anchors
        SET anchor_slug = ?
        WHERE block_id = ? AND anchor_role = 'primary'
    """, (f['new_slug'], f['block_id']))

con.commit()

# ═══════════════════════════════════════════
# 5. VERIFY
# ═══════════════════════════════════════════

# Recount per article
our_by_art_new = defaultdict(int)
for r in con.execute("""
    SELECT anchor_slug, COUNT(*) FROM decision_blocks_resolved
    WHERE anchor_slug IS NOT NULL AND anchor_slug != ''
    GROUP BY anchor_slug
""").fetchall():
    m = re.match(r'cf-1988-art-(\d+)', r[0])
    if m:
        our_by_art_new[int(m.group(1))] += r[1]

# Re-compare with STF
stf_by_art = defaultdict(int)
for art_num, texts in stf_article_texts.items():
    stf_by_art[art_num] = len(texts)

print(f"\nPOS-FIX COMPARISON (divergent only):")
print(f"{'Art':>5s} | {'STF':>5s} | {'Antes':>5s} | {'Agora':>5s} | {'Diff':>6s}")
print("-" * 45)

# Load pre-fix counts
our_by_art_old = defaultdict(int)
for f in fixes:
    our_by_art_old[f['old_art']] += 1

all_affected = set()
for f in fixes:
    all_affected.add(f['old_art'])
    all_affected.add(f['new_art'])

for art in sorted(all_affected):
    s = stf_by_art.get(art, 0)
    before = our_by_art_new.get(art, 0) + sum(1 for f in fixes if f['new_art'] == art) - sum(1 for f in fixes if f['new_art'] == art)
    after = our_by_art_new.get(art, 0)
    d = after - s
    print(f"{art:>5d} | {s:>5d} | {'?':>5s} | {after:>5d} | {d:>+6d}")

con.close()

# Save fix log
fix_log = Path(r"C:\projetos\icons\ingest\fix_fronteiras_log.json")
with open(fix_log, 'w', encoding='utf-8') as f:
    json.dump(fixes, f, ensure_ascii=False, indent=2)

print(f"\nFixes applied: {len(fixes)}")
print(f"Log: {fix_log}")
print("Done.")
