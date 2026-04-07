import csv
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Set


# =========================================================
# UTILITÁRIOS
# =========================================================

def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def normalize_key(text: str) -> str:
    text = normalize_spaces(text)
    text = strip_accents(text).lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def roman_to_int(roman: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(roman.upper()):
        val = values[ch]
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total


def int_to_roman(num: int) -> str:
    pairs = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = []
    n = num
    for val, sym in pairs:
        while n >= val:
            result.append(sym)
            n -= val
    return "".join(result)


def safe_int(value: str):
    try:
        return int(value)
    except Exception:
        return None


# =========================================================
# LEITURA TSV
# =========================================================

def read_tsv(path: Path) -> List[Dict[str, str]]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def write_tsv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
# GERAÇÃO DE VARIANTES
# =========================================================

def variants_artigo(number_norm: str) -> Set[str]:
    n = safe_int(number_norm)
    if n is None:
        return set()
    return {
        f"art. {n}", f"art {n}", f"art. {n}\u00ba", f"art {n}\u00ba",
        f"artigo {n}", f"artigo {n}\u00ba",
    }


def variants_paragrafo(number_raw: str, number_norm: str) -> Set[str]:
    out = set()
    if number_norm == "unico":
        out |= {"par\u00e1grafo \u00fanico", "paragrafo unico", "\u00a7 \u00fanico", "\u00a7 unico"}
        return out
    n = safe_int(number_norm)
    if n is None:
        return out
    out |= {
        f"\u00a7 {n}", f"\u00a7{n}", f"\u00a7 {n}\u00ba", f"\u00a7{n}\u00ba",
        f"par\u00e1grafo {n}", f"paragrafo {n}", f"par {n}",
    }
    return out


def variants_inciso(number_raw: str, number_norm: str) -> Set[str]:
    out = set()
    roman = (number_raw or "").upper().strip()
    n = safe_int(number_norm)
    if n is None and roman:
        try:
            n = roman_to_int(roman)
        except Exception:
            n = None
    if roman:
        out |= {
            roman, f"{roman} -", f"{roman}-", f"{roman} \u2013", f"{roman} \u2014",
            f"inciso {roman}", f"inc. {roman}", f"inc {roman}",
        }
    if n is not None:
        out |= {
            str(n), f"{n} -", f"{n}-", f"inciso {n}", f"inc. {n}", f"inc {n}",
        }
    return out


def variants_alinea(number_raw: str, number_norm: str) -> Set[str]:
    l = (number_norm or number_raw or "").lower().strip()
    if not l:
        return set()
    return {l, f"{l})", f"al\u00ednea {l}", f"alinea {l}", f"ali {l}"}


def variants_item(number_norm: str) -> Set[str]:
    n = safe_int(number_norm)
    if n is None:
        return set()
    return {str(n), f"{n}.", f"item {n}"}


def variants_roman_header(prefix: str, number_raw: str, number_norm: str) -> Set[str]:
    out = set()
    roman = (number_raw or "").upper().strip()
    n = safe_int(number_norm)
    if n is None and roman:
        try:
            n = roman_to_int(roman)
        except Exception:
            n = None
    if roman:
        out.add(f"{prefix} {roman}")
    if n is not None:
        out.add(f"{prefix} {n}")
    return out


def generate_variants(row: Dict[str, str]) -> Set[str]:
    node_type = row["node_type"]
    label = row["label"]
    title = row.get("title", "") or ""
    number_raw = row.get("number_raw", "") or ""
    number_norm = row.get("number_norm", "") or ""

    variants = set()
    if label:
        variants.add(label)
    if title:
        variants.add(title)

    if node_type == "preambulo":
        variants |= {"pre\u00e2mbulo", "preambulo"}
    elif node_type == "titulo":
        variants |= variants_roman_header("t\u00edtulo", number_raw, number_norm)
        variants |= variants_roman_header("titulo", number_raw, number_norm)
    elif node_type == "capitulo":
        variants |= variants_roman_header("cap\u00edtulo", number_raw, number_norm)
        variants |= variants_roman_header("capitulo", number_raw, number_norm)
    elif node_type == "secao":
        variants |= variants_roman_header("se\u00e7\u00e3o", number_raw, number_norm)
        variants |= variants_roman_header("secao", number_raw, number_norm)
    elif node_type == "subsecao":
        variants |= variants_roman_header("subse\u00e7\u00e3o", number_raw, number_norm)
        variants |= variants_roman_header("subsecao", number_raw, number_norm)
    elif node_type == "artigo":
        variants |= variants_artigo(number_norm)
    elif node_type == "paragrafo":
        variants |= variants_paragrafo(number_raw, number_norm)
    elif node_type == "inciso":
        variants |= variants_inciso(number_raw, number_norm)
    elif node_type == "alinea":
        variants |= variants_alinea(number_raw, number_norm)
    elif node_type == "item":
        variants |= variants_item(number_norm)

    return {normalize_key(v) for v in variants if normalize_key(v)}


# =========================================================
# CONSTRUÇÃO DO INDEX
# =========================================================

def build_anchor_index_v2(norm_tree_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out_rows = []

    for row in norm_tree_rows:
        slug = row["slug"]
        node_type = row["node_type"]
        label = row["label"]
        title = row.get("title", "") or ""

        variants = generate_variants(row)

        for variant in sorted(variants):
            key = (variant, slug)
            if key in seen:
                continue
            seen.add(key)

            out_rows.append({
                "anchor_text_norm": variant,
                "slug": slug,
                "label": label,
                "title": title,
                "node_type": node_type,
            })

    return out_rows


# =========================================================
# RELATÓRIO
# =========================================================

def summarize(rows: List[Dict[str, str]]) -> None:
    by_type: Dict[str, int] = {}
    for row in rows:
        by_type[row["node_type"]] = by_type.get(row["node_type"], 0) + 1

    print("\nResumo do norm_anchor_index_v2")
    print("-" * 40)
    print(f"Total de entradas: {len(rows)}")
    for node_type, count in sorted(by_type.items()):
        print(f"  {node_type:12s} {count:>8d}")


# =========================================================
# MAIN
# =========================================================

def main():
    # Try saida_parser first, then ingest root
    input_path = Path(r"C:\projetos\icons\ingest\saida_parser\norm_tree.tsv")
    if not input_path.exists():
        input_path = Path(r"C:\projetos\icons\ingest\norm_tree.tsv")

    output_path = Path(r"C:\projetos\icons\ingest\saida_parser\norm_anchor_index_v2.tsv")

    print(f"Lendo: {input_path}")
    norm_rows = read_tsv(input_path)
    print(f"Nos lidos: {len(norm_rows)}")

    anchor_rows = build_anchor_index_v2(norm_rows)
    write_tsv(output_path, anchor_rows)

    summarize(anchor_rows)
    print(f"\nArquivo salvo em: {output_path}")


if __name__ == "__main__":
    main()
