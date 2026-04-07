"""
Recode decision_blocks_resolved: gera anchor_quality_recode,
anchor_resolution_status e decision_explicitness.
"""
import csv
from pathlib import Path
from typing import Dict, List


BASE = Path(r"C:\projetos\icons\ingest")
INPUT_PATH = BASE / "decision_blocks_resolved.tsv"
OUTPUT_PATH = BASE / "decision_blocks_resolved_recoded.tsv"


# =========================================================
# TSV
# =========================================================

def read_tsv(path: Path) -> List[Dict[str, str]]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def write_tsv(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# =========================================================
# RECODE
# =========================================================

def recode_row(row: Dict[str, str]) -> Dict[str, str]:
    anchor_slug = (row.get("anchor_slug", "") or "").strip()
    anchor_quality = (row.get("anchor_quality", "") or "").strip().lower()
    anchor_source = (row.get("anchor_source", "") or "").strip().lower()

    # 1. anchor_quality_recode
    if not anchor_slug:
        anchor_quality_recode = "unresolved"
    elif anchor_quality == "exact":
        anchor_quality_recode = "exact"
    elif anchor_quality == "adct":
        anchor_quality_recode = "adct"
    elif anchor_quality == "parent":
        anchor_quality_recode = "contextual"
    elif anchor_quality == "unresolved" and anchor_source == "position":
        anchor_quality_recode = "contextual"
    elif anchor_quality == "unresolved" and anchor_source == "hybrid":
        anchor_quality_recode = "exact"
    elif anchor_quality == "unresolved" and anchor_source == "text":
        anchor_quality_recode = "exact"
    elif anchor_slug:
        anchor_quality_recode = "contextual"
    else:
        anchor_quality_recode = "unresolved"

    # 2. anchor_resolution_status
    if anchor_quality_recode == "unresolved":
        anchor_resolution_status = "unresolved"
    else:
        anchor_resolution_status = "resolved"

    # 3. decision_explicitness
    if anchor_source == "text":
        decision_explicitness = "explicit"
    elif anchor_source == "hybrid":
        decision_explicitness = "hybrid"
    elif anchor_source == "position":
        decision_explicitness = "implicit"
    else:
        decision_explicitness = ""

    row["anchor_quality_recode"] = anchor_quality_recode
    row["anchor_resolution_status"] = anchor_resolution_status
    row["decision_explicitness"] = decision_explicitness

    return row


def recode_all(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [recode_row(dict(row)) for row in rows]


# =========================================================
# RESUMO
# =========================================================

def summarize(rows: List[Dict[str, str]]) -> None:
    total = len(rows)

    by_quality: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    by_explicitness: Dict[str, int] = {}

    for row in rows:
        q = row.get("anchor_quality_recode", "")
        s = row.get("anchor_resolution_status", "")
        e = row.get("decision_explicitness", "")

        by_quality[q] = by_quality.get(q, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1
        by_explicitness[e] = by_explicitness.get(e, 0) + 1

    print(f"\nResumo — anchor_quality_recode")
    print("=" * 40)
    for k, v in sorted(by_quality.items()):
        pct = (v / total) * 100 if total else 0
        print(f"  {k:15s} {v:8d}  {pct:6.2f}%")

    print(f"\nResumo — anchor_resolution_status")
    print("=" * 40)
    for k, v in sorted(by_status.items()):
        pct = (v / total) * 100 if total else 0
        print(f"  {k:15s} {v:8d}  {pct:6.2f}%")

    print(f"\nResumo — decision_explicitness")
    print("=" * 40)
    for k, v in sorted(by_explicitness.items()):
        pct = (v / total) * 100 if total else 0
        print(f"  {k:15s} {v:8d}  {pct:6.2f}%")


# =========================================================
# MAIN
# =========================================================

def main():
    rows = read_tsv(INPUT_PATH)
    recoded = recode_all(rows)
    write_tsv(OUTPUT_PATH, recoded)
    summarize(recoded)

    print(f"\nArquivo salvo em: {OUTPUT_PATH}")
    print(f"Registros: {len(recoded)}")


if __name__ == "__main__":
    main()
