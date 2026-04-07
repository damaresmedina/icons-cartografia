import csv
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()

def strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")

def normalize_key(text: str) -> str:
    text = normalize_spaces(text)
    text = strip_accents(text).lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def safe_int(value: str) -> Optional[int]:
    try: return int(value)
    except: return None

def roman_to_int(roman: str) -> int:
    values = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    total = prev = 0
    for ch in reversed(roman.upper()):
        val = values[ch]
        total += -val if val < prev else val
        prev = val
    return total

def read_tsv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def write_tsv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

TOO_AMBIGUOUS = {"i","ii","iii","iv","v","1","2","3","4","5","a","b","c","d","e"}

def is_too_ambiguous(v: str, nt: str) -> bool:
    if v in TOO_AMBIGUOUS: return True
    if re.fullmatch(r"\d+", v): return True
    if re.fullmatch(r"[a-z]", v): return True
    return False

def add_variant(c: List[Tuple[str,str,int]], text: str, origin: str, priority: int):
    n = normalize_key(text)
    if n: c.append((n, origin, priority))

def detect_namespace(row: Dict[str,str]) -> str:
    p = normalize_key(row.get("path",""))
    s = normalize_key(row.get("slug",""))
    return "adct" if "adct" in p or "adct" in s else "cf"

def variants_for_row(row: Dict[str,str]) -> List[Tuple[str,str,int]]:
    nt = row["node_type"]
    label = row.get("label","") or ""
    title = row.get("title","") or ""
    nr = row.get("number_raw","") or ""
    nn = row.get("number_norm","") or ""
    ns = detect_namespace(row)
    out = []

    if label: add_variant(out, label, "label", 100)
    if title: add_variant(out, title, "title", 70)

    if nt == "preambulo":
        add_variant(out, "Pre\u00e2mbulo", "preambulo_formal", 100)
        add_variant(out, "Preambulo", "preambulo_sem_acento", 95)
    elif nt == "titulo":
        if nr: add_variant(out, f"T\u00edtulo {nr}", "titulo_romano", 100); add_variant(out, f"Titulo {nr}", "titulo_romano_sa", 95)
        if nn: add_variant(out, f"T\u00edtulo {nn}", "titulo_arab", 85); add_variant(out, f"Titulo {nn}", "titulo_arab_sa", 80)
    elif nt == "capitulo":
        if nr: add_variant(out, f"Cap\u00edtulo {nr}", "cap_romano", 100); add_variant(out, f"Capitulo {nr}", "cap_romano_sa", 95)
        if nn: add_variant(out, f"Cap\u00edtulo {nn}", "cap_arab", 85); add_variant(out, f"Capitulo {nn}", "cap_arab_sa", 80)
    elif nt == "secao":
        if nr: add_variant(out, f"Se\u00e7\u00e3o {nr}", "sec_romano", 100); add_variant(out, f"Secao {nr}", "sec_romano_sa", 95)
        if nn: add_variant(out, f"Se\u00e7\u00e3o {nn}", "sec_arab", 85); add_variant(out, f"Secao {nn}", "sec_arab_sa", 80)
    elif nt == "subsecao":
        if nr: add_variant(out, f"Subse\u00e7\u00e3o {nr}", "subsec_romano", 100); add_variant(out, f"Subsecao {nr}", "subsec_romano_sa", 95)
        if nn: add_variant(out, f"Subse\u00e7\u00e3o {nn}", "subsec_arab", 80); add_variant(out, f"Subsecao {nn}", "subsec_arab_sa", 75)
    elif nt == "artigo":
        n = safe_int(nn)
        if n is not None:
            add_variant(out, f"Art. {n}\u00ba", "art_formal", 100)
            add_variant(out, f"Art. {n}", "art_sem_ord", 98)
            add_variant(out, f"Art {n}\u00ba", "art_sem_ponto", 95)
            add_variant(out, f"Art {n}", "art_minimo", 93)
            add_variant(out, f"Artigo {n}", "art_extenso", 90)
            if ns == "adct":
                add_variant(out, f"ADCT Art. {n}", "adct_art_formal", 110)
                add_variant(out, f"Art. {n} do ADCT", "adct_art_pos", 108)
    elif nt == "paragrafo":
        if nn == "unico":
            add_variant(out, "Par\u00e1grafo \u00fanico", "par_unico", 100)
            add_variant(out, "Paragrafo unico", "par_unico_sa", 95)
            add_variant(out, "\u00a7 \u00fanico", "par_unico_simb", 90)
        else:
            n = safe_int(nn)
            if n is not None:
                add_variant(out, f"\u00a7 {n}\u00ba", "par_formal", 100)
                add_variant(out, f"\u00a7 {n}", "par_sem_ord", 98)
                add_variant(out, f"\u00a7{n}\u00ba", "par_colado", 96)
                add_variant(out, f"\u00a7{n}", "par_colado_so", 94)
                add_variant(out, f"Par\u00e1grafo {n}", "par_extenso", 88)
                add_variant(out, f"Paragrafo {n}", "par_extenso_sa", 85)
                add_variant(out, f"Par {n}", "par_abrev", 75)
    elif nt == "inciso":
        roman = (nr or "").upper().strip()
        n = safe_int(nn)
        if roman:
            add_variant(out, roman, "inc_romano_nu", 30)
            add_variant(out, f"{roman} -", "inc_romano_hif", 100)
            add_variant(out, f"Inciso {roman}", "inc_romano_ext", 95)
            add_variant(out, f"Inc. {roman}", "inc_romano_abr", 90)
            add_variant(out, f"Inc {roman}", "inc_romano_cur", 88)
        if n is not None:
            add_variant(out, str(n), "inc_arab_nu", 20)
            add_variant(out, f"{n} -", "inc_arab_hif", 97)
            add_variant(out, f"Inciso {n}", "inc_arab_ext", 94)
            add_variant(out, f"Inc. {n}", "inc_arab_abr", 90)
            add_variant(out, f"Inc {n}", "inc_arab_cur", 88)
    elif nt == "alinea":
        l = (nn or nr or "").lower().strip()
        if l:
            add_variant(out, f"{l})", "ali_formal", 100)
            add_variant(out, l, "ali_nua", 15)
            add_variant(out, f"Al\u00ednea {l}", "ali_extenso", 92)
            add_variant(out, f"Alinea {l}", "ali_extenso_sa", 90)
            add_variant(out, f"Ali {l}", "ali_abrev", 75)
    elif nt == "item":
        n = safe_int(nn)
        if n is not None:
            add_variant(out, f"{n}.", "item_formal", 100)
            add_variant(out, str(n), "item_nu", 10)
            add_variant(out, f"Item {n}", "item_extenso", 85)
    return out

def build_anchor_index_v2_1(norm_rows):
    out, seen = [], set()
    for row in norm_rows:
        slug = row["slug"]
        nt = row["node_type"]
        label = row.get("label","") or ""
        title = row.get("title","") or ""
        ns = detect_namespace(row)
        for vn, origin, priority in variants_for_row(row):
            if is_too_ambiguous(vn, nt): continue
            key = (vn, slug)
            if key in seen: continue
            seen.add(key)
            out.append({"anchor_text_norm": vn, "slug": slug, "label": label, "title": title,
                         "node_type": nt, "namespace": ns, "variant_origin": origin, "match_priority": str(priority)})
    out.sort(key=lambda r: (r["anchor_text_norm"], -int(r["match_priority"]), r["slug"]))
    return out

def summarize(rows):
    by_type, by_origin, by_ns = {}, {}, {}
    for r in rows:
        by_type[r["node_type"]] = by_type.get(r["node_type"],0)+1
        by_origin[r["variant_origin"]] = by_origin.get(r["variant_origin"],0)+1
        by_ns[r["namespace"]] = by_ns.get(r["namespace"],0)+1
    print(f"\nResumo norm_anchor_index_v2.1")
    print("="*50)
    print(f"Total: {len(rows)}")
    print("\nPor node_type:")
    for k,v in sorted(by_type.items()): print(f"  {k:14s} {v:>8d}")
    print("\nPor namespace:")
    for k,v in sorted(by_ns.items()): print(f"  {k:14s} {v:>8d}")
    print("\nTop variant_origin:")
    for k,v in sorted(by_origin.items(), key=lambda x: -x[1])[:20]: print(f"  {k:28s} {v:>8d}")

def main():
    # Try saida_parser first
    input_path = Path(r"C:\projetos\icons\ingest\saida_parser\norm_tree.tsv")
    if not input_path.exists():
        input_path = Path(r"C:\projetos\icons\ingest\norm_tree.tsv")
    output_path = Path(r"C:\projetos\icons\ingest\saida_parser\norm_anchor_index_v2_1.tsv")

    print(f"Lendo: {input_path}")
    norm_rows = read_tsv(input_path)
    print(f"Nos: {len(norm_rows)}")
    anchor_rows = build_anchor_index_v2_1(norm_rows)
    write_tsv(output_path, anchor_rows)
    summarize(anchor_rows)
    print(f"\nSalvo: {output_path}")

if __name__ == "__main__":
    main()
