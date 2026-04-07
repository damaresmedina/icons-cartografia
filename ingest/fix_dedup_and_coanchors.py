"""
Fix 1: Deduplicar commentary_blocks.json (remove 46 blocos duplicados slug+texto)
Fix 2: Criar tabela block_anchors no banco (co-ancoragem legítima)
Fix 3: Regravar ESPELHO_MISTO sem duplicatas
"""
import json
import sqlite3
from pathlib import Path
from collections import defaultdict

BASE = Path(r"C:\projetos\icons\ingest\saida_parser")
DB_PATH = BASE / "cf_comentada_v3.db"
JSON_PATH = BASE / "commentary_blocks.json"
JSON_BACKUP = BASE / "commentary_blocks_pre_dedup.json"

# ══════════════════════════════════════════
# 1. DEDUP commentary_blocks.json
# ══════════════════════════════════════════

print("=" * 60)
print("  1. DEDUP commentary_blocks.json")
print("=" * 60)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    blocks = json.load(f)

print(f"  Blocos originais: {len(blocks)}")

# Backup
with open(JSON_BACKUP, "w", encoding="utf-8") as f:
    json.dump(blocks, f, ensure_ascii=False, indent=2)
print(f"  Backup salvo: {JSON_BACKUP}")

# Dedup: keep first occurrence of (anchor_slug, block_text)
seen = set()
deduped = []
removed = 0
for b in blocks:
    key = (b.get("anchor_slug", ""), b.get("block_text", ""))
    if key in seen:
        removed += 1
    else:
        seen.add(key)
        deduped.append(b)

# Reassign block_ids sequentially
for i, b in enumerate(deduped):
    b["block_id"] = i + 1

print(f"  Removidos: {removed}")
print(f"  Blocos finais: {len(deduped)}")

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print(f"  JSON regravado: {JSON_PATH}")


# ══════════════════════════════════════════
# 2. REBUILD commentary_blocks no banco
# ══════════════════════════════════════════

print(f"\n{'=' * 60}")
print("  2. REBUILD commentary_blocks no banco")
print("=" * 60)

con = sqlite3.connect(str(DB_PATH))

# Get existing schema
schema = con.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='commentary_blocks'"
).fetchone()[0]
print(f"  Schema existente OK")

con.execute("DROP TABLE IF EXISTS commentary_blocks_old")
con.execute("ALTER TABLE commentary_blocks RENAME TO commentary_blocks_old")

con.execute(schema)

# Get column names from new table
cols = [r[1] for r in con.execute("PRAGMA table_info(commentary_blocks)").fetchall()]
print(f"  Colunas: {len(cols)}")

# Map JSON keys to DB columns
KEY_MAP = {
    "block_id": "block_id",
    "anchor_slug": "anchor_slug",
    "anchor_slug_original": "anchor_slug",  # fallback
    "anchor_slug_norm": "anchor_slug_norm",
    "match_type": "match_type",
    "node_type": "node_type",
    "node_label": "node_label",
    "anchor_artigo": "anchor_artigo",
    "anchor_paragrafo": "anchor_paragrafo",
    "anchor_inciso": "anchor_inciso",
    "anchor_alinea": "anchor_alinea",
    "editorial_marker": "editorial_marker",
    "block_text": "block_text",
    "metadata_text": "metadata_text",
    "process_class": "process_class",
    "process_number": "process_number",
    "process_full": "process_full",
    "relator": "relator",
    "data_julgamento": "data_julgamento",
    "data_julgamento_raw": "data_julgamento_raw",
    "ano": "ano",
    "tema": "tema",
    "dje": "dje",
}

placeholders = ",".join("?" for _ in cols)
insert_sql = f"INSERT INTO commentary_blocks ({','.join(cols)}) VALUES ({placeholders})"

rows_inserted = 0
for b in deduped:
    values = []
    for col in cols:
        val = b.get(col, "")
        if val is None:
            val = ""
        values.append(val)
    con.execute(insert_sql, values)
    rows_inserted += 1

con.commit()
print(f"  Inseridos: {rows_inserted}")

# Drop old
con.execute("DROP TABLE IF EXISTS commentary_blocks_old")


# ══════════════════════════════════════════
# 3. CREATE block_anchors TABLE
# ══════════════════════════════════════════

print(f"\n{'=' * 60}")
print("  3. CREATE block_anchors")
print("=" * 60)

con.execute("DROP TABLE IF EXISTS block_anchors")
con.execute("""
    CREATE TABLE block_anchors (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id        INTEGER NOT NULL,
        anchor_slug     TEXT NOT NULL,
        anchor_role     TEXT DEFAULT 'primary',
        confidence      REAL,
        source          TEXT,
        FOREIGN KEY (block_id) REFERENCES decision_blocks_resolved(block_id)
    )
""")

# Populate: primary anchors from decision_blocks_resolved
con.execute("""
    INSERT INTO block_anchors (block_id, anchor_slug, anchor_role, confidence, source)
    SELECT block_id, anchor_slug, 'primary', anchor_confidence, anchor_source
    FROM decision_blocks_resolved
    WHERE anchor_slug IS NOT NULL AND anchor_slug != ''
""")
primary_count = con.execute("SELECT COUNT(*) FROM block_anchors").fetchone()[0]
print(f"  Primary anchors: {primary_count}")

# Detect co-anchors: same block_text appearing under different slugs
# For each text that appears in multiple slugs, add secondary anchors
text_to_entries = defaultdict(list)
for row in con.execute("""
    SELECT block_id, anchor_slug, block_text, anchor_confidence, anchor_source
    FROM decision_blocks_resolved
    WHERE block_text IS NOT NULL AND block_text != ''
""").fetchall():
    text_to_entries[row[2]].append({
        "block_id": row[0], "slug": row[1], "conf": row[3], "src": row[4]
    })

co_anchor_count = 0
for text, entries in text_to_entries.items():
    if len(entries) <= 1:
        continue
    # All slugs for this text
    all_slugs = set(e["slug"] for e in entries)
    if len(all_slugs) <= 1:
        continue
    # For each entry, add the OTHER slugs as secondary anchors
    for entry in entries:
        other_slugs = all_slugs - {entry["slug"]}
        for other_slug in other_slugs:
            con.execute(
                "INSERT INTO block_anchors (block_id, anchor_slug, anchor_role, confidence, source) "
                "VALUES (?, ?, 'secondary', ?, ?)",
                (entry["block_id"], other_slug, entry["conf"], entry["src"])
            )
            co_anchor_count += 1

print(f"  Secondary (co-anchors): {co_anchor_count}")

# Indexes
con.execute("CREATE INDEX idx_ba_block ON block_anchors(block_id)")
con.execute("CREATE INDEX idx_ba_slug ON block_anchors(anchor_slug)")
con.execute("CREATE INDEX idx_ba_role ON block_anchors(anchor_role)")

# Summary view
con.execute("DROP VIEW IF EXISTS v_block_anchor_summary")
con.execute("""
    CREATE VIEW v_block_anchor_summary AS
    SELECT
        anchor_role,
        COUNT(*) as total,
        COUNT(DISTINCT block_id) as unique_blocks,
        COUNT(DISTINCT anchor_slug) as unique_slugs
    FROM block_anchors
    GROUP BY anchor_role
""")

con.commit()

# Verify
print(f"\n  === block_anchors summary ===")
for r in con.execute("SELECT * FROM v_block_anchor_summary"):
    print(f"    {r[0]:12s} total={r[1]:6d}  blocks={r[2]:6d}  slugs={r[3]:5d}")

total_ba = con.execute("SELECT COUNT(*) FROM block_anchors").fetchone()[0]
print(f"  Total anchors: {total_ba}")

con.close()

import os
print(f"\n  DB: {DB_PATH} ({os.path.getsize(str(DB_PATH))/1024/1024:.1f} MB)")
print(f"  Pronto.")
