"""
Expande o norm_anchor_index.tsv com variantes de inciso, paragrafo e alinea.
Depois re-roda o populate_db.py com o index expandido.
"""
import csv, re, os
from pathlib import Path

BASE = os.path.join("C:", os.sep, "projetos", "icons", "ingest", "saida_parser")

# Roman numeral table
ROMAN = {
    "I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,"VII":7,"VIII":8,"IX":9,"X":10,
    "XI":11,"XII":12,"XIII":13,"XIV":14,"XV":15,"XVI":16,"XVII":17,"XVIII":18,
    "XIX":19,"XX":20,"XXI":21,"XXII":22,"XXIII":23,"XXIV":24,"XXV":25,
    "XXVI":26,"XXVII":27,"XXVIII":28,"XXIX":29,"XXX":30,"XXXI":31,"XXXII":32,
    "XXXIII":33,"XXXIV":34,"XXXV":35,"XXXVI":36,"XXXVII":37,"XXXVIII":38,
    "XXXIX":39,"XL":40,"XLI":41,"XLII":42,"XLIII":43,"XLIV":44,"XLV":45,
    "XLVI":46,"XLVII":47,"XLVIII":48,"XLIX":49,"L":50,"LI":51,"LII":52,
    "LIII":53,"LIV":54,"LV":55,"LVI":56,"LVII":57,"LVIII":58,"LIX":59,
    "LX":60,"LXI":61,"LXII":62,"LXIII":63,"LXIV":64,"LXV":65,"LXVI":66,
    "LXVII":67,"LXVIII":68,"LXIX":69,"LXX":70,"LXXI":71,"LXXII":72,
    "LXXIII":73,"LXXIV":74,"LXXV":75,"LXXVI":76,"LXXVII":77,"LXXVIII":78,
}
INT_TO_ROMAN = {v: k for k, v in ROMAN.items()}

# Read existing index
tsv_path = os.path.join(BASE, "norm_anchor_index.tsv")
with open(tsv_path, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter="\t")
    original_rows = list(reader)

print(f"Index original: {len(original_rows)} entradas")

# Build expanded index
expanded = {}  # anchor_text_norm -> {slug, label, node_type}

# Keep all originals
for r in original_rows:
    key = r["anchor_text_norm"].strip().lower()
    expanded[key] = {
        "slug": r["slug"],
        "label": r["label"],
        "node_type": r["node_type"],
    }

# Now expand variants for each node
for r in original_rows:
    slug = r["slug"]
    node_type = r["node_type"]
    label = r["label"]

    if node_type == "inciso":
        # Extract number from slug: cf-1988-art-5-inc-14
        m = re.search(r'-inc-(\d+)$', slug)
        if not m:
            continue
        n = int(m.group(1))
        roman = INT_TO_ROMAN.get(n, str(n))

        variants = [
            roman.lower(),
            f"{roman.lower()} -",
            f"{roman.lower()} \u2013",
            f"{roman.lower()} \u2014",
            str(n),
            f"{n} -",
            f"inc {n}",
            f"inciso {n}",
            f"inciso {roman.lower()}",
            f"inc {roman.lower()}",
        ]
        for v in variants:
            v_norm = v.strip().lower()
            if v_norm and v_norm not in expanded:
                expanded[v_norm] = {"slug": slug, "label": label, "node_type": node_type}

    elif node_type == "paragrafo":
        # Extract from slug: cf-1988-art-5-par-1 or par-unico
        m = re.search(r'-par-(\w+)$', slug)
        if not m:
            continue
        n = m.group(1)

        if n == "unico":
            variants = [
                "paragrafo unico",
                "paragrafo unico",
                "par unico",
                "paragrafo unico",
            ]
        else:
            variants = [
                f"\u00a7 {n}",
                f"\u00a7{n}",
                f"\u00a7 {n}\u00ba",
                f"paragrafo {n}",
                f"paragrafo {n}",
                f"par {n}",
                str(n),
            ]
        for v in variants:
            v_norm = v.strip().lower()
            if v_norm and v_norm not in expanded:
                expanded[v_norm] = {"slug": slug, "label": label, "node_type": node_type}

    elif node_type == "alinea":
        # Extract from slug: cf-1988-art-5-inc-28-ali-a
        m = re.search(r'-ali-(\w)$', slug)
        if not m:
            continue
        l = m.group(1)

        variants = [
            f"{l})",
            l,
            f"alinea {l}",
            f"alinea {l}",
            f"ali {l}",
        ]
        for v in variants:
            v_norm = v.strip().lower()
            if v_norm and v_norm not in expanded:
                expanded[v_norm] = {"slug": slug, "label": label, "node_type": node_type}

print(f"Index expandido: {len(expanded)} entradas (+{len(expanded) - len(original_rows)})")

# Count by type
type_count = {}
for v in expanded.values():
    t = v["node_type"]
    type_count[t] = type_count.get(t, 0) + 1
print(f"Por tipo: {type_count}")

# Save expanded index
out_path = os.path.join(BASE, "norm_anchor_index.tsv")
# Backup original
backup_path = os.path.join(BASE, "norm_anchor_index_original.tsv")
if not os.path.exists(backup_path):
    import shutil
    shutil.copy2(out_path, backup_path)
    print(f"Backup salvo: {backup_path}")

with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["anchor_text_norm", "slug", "label", "node_type"], delimiter="\t")
    writer.writeheader()
    for anchor_text, meta in sorted(expanded.items()):
        writer.writerow({
            "anchor_text_norm": anchor_text,
            "slug": meta["slug"],
            "label": meta["label"],
            "node_type": meta["node_type"],
        })

print(f"Index expandido salvo: {out_path}")
