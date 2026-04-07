"""Parse STF Constituição e o Supremo HTML para extrair estrutura de artigos e decisões."""
import re
import json
from html.parser import HTMLParser
from collections import defaultdict
from pathlib import Path

HTML_PATH = Path(r"C:\projetos\icons\ingest\stf_constituicao_raw.html")
OUT_PATH = Path(r"C:\projetos\icons\ingest\stf_structure.json")

html = HTML_PATH.read_text(encoding="utf-8", errors="replace")

# Extract article sections using regex on the HTML structure
# Articles are typically marked with id patterns like "art1", "art2", etc.
# Decisions/comments are in divs with class "com" or similar

# 1. Find all article markers
art_pattern = re.compile(
    r'id="art(\d+[a-z]*)"[^>]*>.*?<[^>]*>[\s]*(Art\.?\s*\d+[^<]*)',
    re.IGNORECASE | re.DOTALL
)

# 2. Find editorial sections (SV, CC, RG, JC)
editorial_patterns = {
    'sumula_vinculante': re.compile(r'Súmula\s+Vinculante', re.IGNORECASE),
    'controle_concentrado': re.compile(r'Controle\s+[Cc]oncentrado', re.IGNORECASE),
    'repercussao_geral': re.compile(r'Repercussão\s+[Gg]eral', re.IGNORECASE),
    'julgados_correlatos': re.compile(r'Julgados?\s+[Cc]orrelatos?', re.IGNORECASE),
}

# 3. Find comment blocks (decisions)
com_pattern = re.compile(r'<div\s+class="com"\s+id="com(\d+)"', re.IGNORECASE)

# Simple approach: split by article markers and count decisions per article
# Find all article headers
art_headers = re.findall(
    r'<(?:h\d|div|p|span)[^>]*id="(art\d+[^"]*)"[^>]*>(.*?)</(?:h\d|div|p|span)>',
    html, re.IGNORECASE | re.DOTALL
)

print(f"Article headers found: {len(art_headers)}")

# Better: find all elements with id starting with "art"
art_ids = re.findall(r'id="(art\d+[a-z]*)"', html, re.IGNORECASE)
art_ids_unique = list(dict.fromkeys(art_ids))  # preserve order, remove dupes
print(f"Unique article IDs: {len(art_ids_unique)}")

# Find all comment IDs
com_ids = re.findall(r'id="com(\d+)"', html)
print(f"Total comment/decision blocks: {len(com_ids)}")

# Now map each comment to its parent article
# Strategy: for each article id position in HTML, find how many comments come before the next article
art_positions = [(m.start(), m.group(1)) for m in re.finditer(r'id="(art\d+[a-z]*)"', html, re.IGNORECASE)]
com_positions = [(m.start(), m.group(1)) for m in re.finditer(r'id="com(\d+)"', html)]

print(f"\nArticle positions: {len(art_positions)}")
print(f"Comment positions: {len(com_positions)}")

# Assign comments to articles based on position in HTML
art_comments = defaultdict(list)
art_idx = 0
for com_pos, com_id in com_positions:
    # Find which article this comment belongs to
    while art_idx < len(art_positions) - 1 and art_positions[art_idx + 1][0] < com_pos:
        art_idx += 1
    if art_idx < len(art_positions):
        art_id = art_positions[art_idx][1]
        art_comments[art_id].append(com_id)

# Extract article labels
art_labels = {}
for art_id in art_ids_unique:
    # Find the text near this id
    pattern = re.compile(rf'id="{re.escape(art_id)}"[^>]*>(.*?)</', re.DOTALL)
    m = pattern.search(html)
    if m:
        label = re.sub(r'<[^>]+>', '', m.group(1)).strip()[:100]
        art_labels[art_id] = label

# Count editorial markers per article section
art_editorials = defaultdict(lambda: defaultdict(int))
for i, (pos, art_id) in enumerate(art_positions):
    next_pos = art_positions[i + 1][0] if i + 1 < len(art_positions) else len(html)
    section = html[pos:next_pos]
    for ed_name, ed_re in editorial_patterns.items():
        count = len(ed_re.findall(section))
        if count:
            art_editorials[art_id][ed_name] = count

# Build output
structure = []
for art_id in art_ids_unique:
    entry = {
        "art_id": art_id,
        "label": art_labels.get(art_id, ""),
        "decisions": len(art_comments.get(art_id, [])),
        "editorials": dict(art_editorials.get(art_id, {})),
    }
    structure.append(entry)

# Summary
total_decisions = sum(e["decisions"] for e in structure)
arts_with_decisions = sum(1 for e in structure if e["decisions"] > 0)

print(f"\n{'='*60}")
print(f"  ESTRUTURA STF ONLINE")
print(f"{'='*60}")
print(f"  Artigos: {len(structure)}")
print(f"  Artigos com decisoes: {arts_with_decisions}")
print(f"  Total decisoes: {total_decisions}")
print(f"\n  Top 20 artigos por decisoes:")
for e in sorted(structure, key=lambda x: -x["decisions"])[:20]:
    eds = ", ".join(f"{k}:{v}" for k, v in e["editorials"].items()) if e["editorials"] else ""
    print(f"    {e['art_id']:15s} {e['decisions']:4d} decisoes  {eds}")

# Save
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(structure, f, ensure_ascii=False, indent=2)
print(f"\n  Salvo: {OUT_PATH}")
