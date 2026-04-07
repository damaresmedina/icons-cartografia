import csv
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()

def strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")

def normalize_key(text: str) -> str:
    text = normalize_spaces(text)
    text = strip_accents(text).lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", text).strip()

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

RE_ADCT = re.compile(r"\bADCT\b", re.IGNORECASE)
RE_ARTIGO = re.compile(r"\bArt\.?\s*(\d+)(?:[\u00bao\u00b0])?\b", re.IGNORECASE)
RE_PARAGRAFO = re.compile(r"\u00a7\s*(\d+)(?:[\u00bao\u00b0])?", re.IGNORECASE)
RE_PAR_UNICO = re.compile(r"Par[a\u00e1]grafo\s+[u\u00fa]nico", re.IGNORECASE)
RE_INCISO_ROMANO = re.compile(r"\b([IVXLCDM]+)\s*[-\u2013\u2014]", re.IGNORECASE)
RE_INCISO_EXTENSO_ROMANO = re.compile(r"\binc(?:iso|\.)?\s+([IVXLCDM]+)\b", re.IGNORECASE)
RE_INCISO_EXTENSO_ARABICO = re.compile(r"\binc(?:iso|\.)?\s+(\d+)\b", re.IGNORECASE)
RE_ALINEA = re.compile(r"\b([a-z])\)", re.IGNORECASE)
RE_ALINEA_EXTENSO = re.compile(r"\bal[i\u00ed]nea\s+([a-z])\b", re.IGNORECASE)
RE_TITULO = re.compile(r"\bT[\u00edi]tulo\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)
RE_CAPITULO = re.compile(r"\bCap[\u00edi]tulo\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)
RE_SECAO = re.compile(r"\bSe[c\u00e7][a\u00e3]o\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)
RE_SUBSECAO = re.compile(r"\bSubse[c\u00e7][a\u00e3]o\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)

NODE_SPECIFICITY = {"alinea":100,"item":95,"inciso":90,"paragrafo":85,"artigo":80,"subsecao":70,"secao":65,"capitulo":60,"titulo":55,"preambulo":50}

def build_anchor_lookup(rows):
    lookup = {}
    for r in rows:
        lookup.setdefault(r["anchor_text_norm"], []).append(r)
    for k in lookup:
        lookup[k].sort(key=lambda r: (-int(r.get("match_priority","0")), r.get("node_type",""), r.get("slug","")))
    return lookup

def build_parent_map(rows):
    return {r["slug"]: r.get("parent_slug","") for r in rows}

def build_slug_map(rows):
    return {r["slug"]: r for r in rows}

def detect_namespace(text):
    return "adct" if RE_ADCT.search(text) else "cf"

def extract_anchor_candidates(text):
    candidates = []
    for m in RE_ARTIGO.finditer(text):
        n = m.group(1)
        candidates.extend([f"Art. {n}\u00ba", f"Art. {n}", f"Artigo {n}"])
    if RE_PAR_UNICO.search(text):
        candidates.extend(["Par\u00e1grafo \u00fanico", "Paragrafo unico", "\u00a7 \u00fanico"])
    for m in RE_PARAGRAFO.finditer(text):
        n = m.group(1)
        candidates.extend([f"\u00a7 {n}\u00ba", f"\u00a7 {n}", f"Par\u00e1grafo {n}", f"Paragrafo {n}", f"Par {n}"])
    for m in RE_INCISO_ROMANO.finditer(text):
        r = m.group(1).upper()
        candidates.extend([f"{r} -", f"Inciso {r}", f"Inc. {r}", f"Inc {r}"])
    for m in RE_INCISO_EXTENSO_ROMANO.finditer(text):
        r = m.group(1).upper()
        candidates.extend([f"Inciso {r}", f"Inc. {r}", f"Inc {r}", f"{r} -"])
    for m in RE_INCISO_EXTENSO_ARABICO.finditer(text):
        n = m.group(1)
        candidates.extend([f"Inciso {n}", f"Inc. {n}", f"Inc {n}", f"{n} -"])
    for m in RE_ALINEA.finditer(text):
        l = m.group(1).lower()
        candidates.extend([f"{l})", f"Al\u00ednea {l}", f"Alinea {l}", f"Ali {l}"])
    for m in RE_ALINEA_EXTENSO.finditer(text):
        l = m.group(1).lower()
        candidates.extend([f"Al\u00ednea {l}", f"Alinea {l}", f"Ali {l}", f"{l})"])
    for m in RE_TITULO.finditer(text):
        x = m.group(1)
        candidates.extend([f"T\u00edtulo {x}", f"Titulo {x}"])
    for m in RE_CAPITULO.finditer(text):
        x = m.group(1)
        candidates.extend([f"Cap\u00edtulo {x}", f"Capitulo {x}"])
    for m in RE_SECAO.finditer(text):
        x = m.group(1)
        candidates.extend([f"Se\u00e7\u00e3o {x}", f"Secao {x}"])
    for m in RE_SUBSECAO.finditer(text):
        x = m.group(1)
        candidates.extend([f"Subse\u00e7\u00e3o {x}", f"Subsecao {x}"])
    seen = set()
    out = []
    for c in candidates:
        k = normalize_key(c)
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out

def compute_confidence(best, exact, ns_match):
    nt = best.get("node_type","")
    pri = int(best.get("match_priority","0"))
    base = 0.90 if exact else 0.70
    if ns_match: base += 0.05
    base += {"alinea":0.04,"inciso":0.03,"paragrafo":0.025,"artigo":0.02}.get(nt, 0)
    if pri >= 100: base += 0.03
    elif pri >= 90: base += 0.02
    elif pri >= 80: base += 0.01
    return f"{min(base, 1.0):.3f}"

def choose_best_candidate(candidates, lookup, expected_ns):
    matches = []
    for c in candidates:
        norm = normalize_key(c)
        if norm not in lookup: continue
        for row in lookup[norm]:
            score = int(row.get("match_priority","0")) + NODE_SPECIFICITY.get(row.get("node_type",""),0)
            if row.get("namespace","") == expected_ns: score += 50
            else: score -= 20
            matches.append((score, c, row))
    if not matches: return None
    matches.sort(key=lambda x: (-x[0], -int(x[2].get("match_priority","0")), x[2].get("slug","")))
    _, matched_var, best_row = matches[0]
    result = dict(best_row)
    result["_matched_variant"] = matched_var
    result["_score"] = str(matches[0][0])
    return result

def match_block(block_text, metadata_text, lookup, parent_map, slug_map):
    merged = (block_text + "\n" + metadata_text).strip()
    ns = detect_namespace(merged)
    candidates = extract_anchor_candidates(merged)
    best = choose_best_candidate(candidates, lookup, ns)

    if best:
        ns_match = best.get("namespace","") == ns
        return {
            "anchor_slug": best["slug"], "anchor_label": best.get("label",""),
            "anchor_node_type": best.get("node_type",""), "anchor_namespace": best.get("namespace",""),
            "anchor_quality": "exact" if ns_match else "adct",
            "anchor_confidence": compute_confidence(best, exact=True, ns_match=ns_match),
            "matched_variant": best.get("_matched_variant",""), "variant_origin": best.get("variant_origin",""),
            "match_priority": best.get("match_priority",""), "match_score": best.get("_score",""),
        }

    art_m = RE_ARTIGO.search(merged)
    if art_m:
        ac = normalize_key(f"Art. {art_m.group(1)}\u00ba")
        rows = lookup.get(ac, [])
        if rows:
            chosen = None
            for r in rows:
                if r.get("node_type") == "artigo":
                    if r.get("namespace") == ns: chosen = r; break
                    if not chosen: chosen = r
            if chosen:
                return {
                    "anchor_slug": chosen["slug"], "anchor_label": chosen.get("label",""),
                    "anchor_node_type": chosen.get("node_type",""), "anchor_namespace": chosen.get("namespace",""),
                    "anchor_quality": "parent", "anchor_confidence": "0.800",
                    "matched_variant": f"Art. {art_m.group(1)}\u00ba", "variant_origin": chosen.get("variant_origin",""),
                    "match_priority": chosen.get("match_priority",""), "match_score": "",
                }

    return {
        "anchor_slug": "", "anchor_label": "", "anchor_node_type": "", "anchor_namespace": ns,
        "anchor_quality": "unresolved", "anchor_confidence": "",
        "matched_variant": "", "variant_origin": "", "match_priority": "", "match_score": "",
    }

def process_blocks(blocks_rows, lookup, parent_map, slug_map):
    out = []
    for row in blocks_rows:
        result = match_block(
            row.get("text","") or row.get("block_text","") or "",
            row.get("metadata_text","") or "",
            lookup, parent_map, slug_map,
        )
        merged = dict(row)
        merged.update(result)
        out.append(merged)
    return out

def main():
    base = Path(r"C:\projetos\icons\ingest\saida_parser")
    norm_tree_path = base / "norm_tree.tsv"
    anchor_index_path = base / "norm_anchor_index_v2_1.tsv"
    if not anchor_index_path.exists():
        anchor_index_path = base / "norm_anchor_index.tsv"
    blocks_path = base / "commentary_blocks.tsv"
    output_path = base / "commentary_blocks_matched_v2_1.tsv"

    print(f"norm_tree: {norm_tree_path}")
    print(f"anchor_index: {anchor_index_path}")
    print(f"blocks: {blocks_path}")

    norm_rows = read_tsv(norm_tree_path)
    anchor_rows = read_tsv(anchor_index_path)
    blocks_rows = read_tsv(blocks_path)

    print(f"\nNos: {len(norm_rows)}")
    print(f"Ancoras: {len(anchor_rows)}")
    print(f"Blocos: {len(blocks_rows)}")

    lookup = build_anchor_lookup(anchor_rows)
    parent_map = build_parent_map(norm_rows)
    slug_map = build_slug_map(norm_rows)

    matched = process_blocks(blocks_rows, lookup, parent_map, slug_map)
    write_tsv(output_path, matched)

    # Stats
    from collections import Counter
    quals = Counter(r.get("anchor_quality","") for r in matched)
    nts = Counter(r.get("anchor_node_type","") for r in matched if r.get("anchor_slug"))
    confs = [float(r["anchor_confidence"]) for r in matched if r.get("anchor_confidence")]

    print(f"\n=== RESULTADO ===")
    print(f"Total: {len(matched)}")
    print(f"\nPor qualidade:")
    for q, n in quals.most_common():
        print(f"  {q or 'vazio':15s} {n:5d} ({n/len(matched)*100:.1f}%)")
    print(f"\nPor node_type:")
    for t, n in nts.most_common():
        print(f"  {t:15s} {n:5d}")
    if confs:
        print(f"\nConfidence media: {sum(confs)/len(confs):.3f}")
        print(f"Confidence min:   {min(confs):.3f}")
        print(f"Confidence max:   {max(confs):.3f}")

    print(f"\nSalvo: {output_path}")

if __name__ == "__main__":
    main()
