"""
Unifica parser (posição) + matcher (texto) em anchor_source + anchor_confidence_final.
Lê:
  - commentary_blocks.json (parser v8 — âncora por posição)
  - commentary_blocks_matched_v2_1.tsv (matcher — âncora por texto)
  - decision_blocks_resolved.tsv (v2.2-b)
Produz:
  - decision_blocks_unified.tsv (com anchor_source e confidence_final)
  - Atualiza cf_comentada_v3.db com tabela e views
"""
import csv, json, re, os, sqlite3
from pathlib import Path
from collections import Counter

BASE = Path("C:", "/", "projetos", "icons", "ingest", "saida_parser")

def read_tsv(path):
    with open(str(path), "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def write_tsv(path, rows):
    if not rows: return
    with open(str(path), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

def normalize_slug(s):
    if not s: return ""
    s = s.strip().lower()
    s = re.sub(r'^cf-art-', 'cf-1988-art-', s) if s.startswith('cf-art-') else s
    return s

# ══════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════

print("Carregando dados...")

# Parser anchors (by position)
with open(str(BASE / "commentary_blocks.json"), "r", encoding="utf-8") as f:
    parser_blocks = json.load(f)

parser_map = {}
for b in parser_blocks:
    bid = b.get("block_id")
    slug = normalize_slug(b.get("anchor_slug", ""))
    parser_map[str(bid)] = {
        "parser_slug": slug,
        "parser_artigo": b.get("anchor_artigo"),
        "parser_inciso": b.get("anchor_inciso"),
        "parser_paragrafo": b.get("anchor_paragrafo"),
    }

# Matcher anchors (by text)
matcher_rows = read_tsv(BASE / "commentary_blocks_matched_v2_1.tsv")
matcher_map = {}
for r in matcher_rows:
    bid = r.get("block_id", "")
    slug = r.get("anchor_slug", "").strip()
    quality = r.get("anchor_quality", "")
    conf = r.get("anchor_confidence", "")
    matcher_map[bid] = {
        "matcher_slug": slug,
        "matcher_quality": quality,
        "matcher_confidence": conf,
    }

# Decision blocks resolved
resolved_rows = read_tsv(BASE / "decision_blocks_resolved.tsv")
print(f"  Parser blocks: {len(parser_map)}")
print(f"  Matcher blocks: {len(matcher_map)}")
print(f"  Resolved blocks: {len(resolved_rows)}")

# ══════════════════════════════════════════
# UNIFY
# ══════════════════════════════════════════

print("\nUnificando...")

unified = []
stats = Counter()

for r in resolved_rows:
    bid = r.get("block_id", "")

    p = parser_map.get(bid, {})
    m = matcher_map.get(bid, {})

    parser_slug = p.get("parser_slug", "")
    matcher_slug = m.get("matcher_slug", "")
    matcher_quality = m.get("matcher_quality", "")

    # Normalize for comparison
    parser_norm = normalize_slug(parser_slug)
    matcher_norm = normalize_slug(matcher_slug)

    # Determine anchor_source
    if matcher_norm and parser_norm:
        # Both have anchors
        if matcher_norm == parser_norm or matcher_norm.startswith(parser_norm) or parser_norm.startswith(matcher_norm):
            anchor_source = "hybrid"
            anchor_slug_final = matcher_norm if len(matcher_norm) >= len(parser_norm) else parser_norm
            confidence_final = 1.0
        else:
            # Disagree — trust parser (position) for article, matcher for specificity
            anchor_source = "position"
            anchor_slug_final = parser_norm
            confidence_final = 0.85
    elif matcher_norm and matcher_quality != "unresolved":
        anchor_source = "text"
        anchor_slug_final = matcher_norm
        try:
            confidence_final = float(m.get("matcher_confidence", "0.95"))
        except:
            confidence_final = 0.95
    elif parser_norm:
        anchor_source = "position"
        anchor_slug_final = parser_norm
        confidence_final = 0.87
    else:
        anchor_source = "unresolved"
        anchor_slug_final = ""
        confidence_final = 0.0

    stats[anchor_source] += 1

    # Update resolved row
    r["anchor_slug_final"] = anchor_slug_final
    r["anchor_source"] = anchor_source
    r["anchor_confidence_final"] = f"{confidence_final:.3f}"
    r["parser_slug"] = parser_norm
    r["matcher_slug"] = matcher_norm

    unified.append(r)

# ══════════════════════════════════════════
# SAVE TSV
# ══════════════════════════════════════════

out_path = BASE / "decision_blocks_unified.tsv"
write_tsv(out_path, unified)

# ══════════════════════════════════════════
# UPDATE DB
# ══════════════════════════════════════════

DB = BASE / "cf_comentada_v3.db"
print(f"\nAtualizando DB: {DB}")
con = sqlite3.connect(str(DB))

con.execute("DROP TABLE IF EXISTS decision_blocks_unified")
cols = list(unified[0].keys())
col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
con.execute(f'CREATE TABLE decision_blocks_unified ({col_defs})')

placeholders = ",".join("?" for _ in cols)
con.executemany(
    "INSERT INTO decision_blocks_unified (" + ",".join('"' + c + '"' for c in cols) + ") VALUES (" + placeholders + ")",
    [[r.get(c, "") for c in cols] for r in unified]
)

# Indexes
con.execute('CREATE INDEX IF NOT EXISTS idx_dbu_slug ON decision_blocks_unified(anchor_slug_final)')
con.execute('CREATE INDEX IF NOT EXISTS idx_dbu_source ON decision_blocks_unified(anchor_source)')
con.execute('CREATE INDEX IF NOT EXISTS idx_dbu_relator ON decision_blocks_unified(relator)')
con.execute('CREATE INDEX IF NOT EXISTS idx_dbu_pkey ON decision_blocks_unified(process_key)')
con.execute('CREATE INDEX IF NOT EXISTS idx_dbu_dut ON decision_blocks_unified(decision_unit_type)')

# Views
con.execute("DROP VIEW IF EXISTS v_anchor_source_distribution")
con.execute("""
CREATE VIEW v_anchor_source_distribution AS
SELECT anchor_source, COUNT(*) as blocks,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM decision_blocks_unified), 1) as pct
FROM decision_blocks_unified
GROUP BY anchor_source
""")

con.execute("DROP VIEW IF EXISTS v_anchor_source_by_relator")
con.execute("""
CREATE VIEW v_anchor_source_by_relator AS
SELECT relator, anchor_source, COUNT(*) as blocks
FROM decision_blocks_unified
WHERE relator IS NOT NULL AND relator != ''
GROUP BY relator, anchor_source
ORDER BY relator, blocks DESC
""")

con.execute("DROP VIEW IF EXISTS v_relator_anchor_unified")
con.execute("""
CREATE VIEW v_relator_anchor_unified AS
SELECT relator, anchor_slug_final, decision_unit_type, anchor_source,
       COUNT(*) as blocks, COUNT(DISTINCT process_key) as distinct_procs,
       ROUND(AVG(CAST(anchor_confidence_final AS REAL)), 3) as avg_confidence
FROM decision_blocks_unified
WHERE relator IS NOT NULL AND relator != '' AND anchor_slug_final != ''
GROUP BY relator, anchor_slug_final, decision_unit_type, anchor_source
""")

con.execute("DROP VIEW IF EXISTS v_process_network_unified")
con.execute("""
CREATE VIEW v_process_network_unified AS
SELECT process_key, process_class, relator,
       COUNT(*) as blocks, COUNT(DISTINCT anchor_slug_final) as distinct_anchors,
       GROUP_CONCAT(DISTINCT anchor_slug_final) as anchor_slugs,
       anchor_source
FROM decision_blocks_unified
WHERE process_key IS NOT NULL AND process_key != ''
GROUP BY process_key, process_class, relator, anchor_source
""")

con.commit()

# ══════════════════════════════════════════
# DIAGNOSTICO
# ══════════════════════════════════════════

total = len(unified)
print(f"\n{'='*70}")
print(f"  DECISION BLOCKS UNIFIED")
print(f"{'='*70}")
print(f"  Total: {total}")

print(f"\n  Por anchor_source:")
for src, n in stats.most_common():
    print(f"    {src:15s} {n:5d} ({n/total*100:.1f}%)")

# Confidence by source
for src in ['hybrid', 'text', 'position', 'unresolved']:
    confs = [float(r['anchor_confidence_final']) for r in unified if r['anchor_source'] == src and r['anchor_confidence_final']]
    if confs:
        print(f"  Confidence {src}: avg={sum(confs)/len(confs):.3f} min={min(confs):.3f} max={max(confs):.3f}")

# Global confidence
all_confs = [float(r['anchor_confidence_final']) for r in unified if r['anchor_confidence_final']]
print(f"\n  Confidence global: {sum(all_confs)/len(all_confs):.3f}")

# Views
for v in ['v_anchor_source_distribution', 'v_anchor_source_by_relator', 'v_relator_anchor_unified', 'v_process_network_unified']:
    cnt = con.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
    print(f"  {v}: {cnt} linhas")

# Sample: anchor_source distribution
print(f"\n  Distribuicao anchor_source:")
for r in con.execute("SELECT * FROM v_anchor_source_distribution").fetchall():
    print(f"    {r[0]:15s} {r[1]:5d} ({r[2]}%)")

# Top 5 relatores by source
print(f"\n  Top relatores por source (hibrido):")
for r in con.execute("SELECT relator, blocks FROM v_anchor_source_by_relator WHERE anchor_source='hybrid' ORDER BY blocks DESC LIMIT 5").fetchall():
    print(f"    {r[0]:30s} {r[1]:5d}")

print(f"\n  Top relatores por source (posicao):")
for r in con.execute("SELECT relator, blocks FROM v_anchor_source_by_relator WHERE anchor_source='position' ORDER BY blocks DESC LIMIT 5").fetchall():
    print(f"    {r[0]:30s} {r[1]:5d}")

con.close()

print(f"\n  TSV: {out_path}")
print(f"  DB: {DB} ({os.path.getsize(str(DB))/1024/1024:.1f} MB)")
print(f"  Pronto.")
