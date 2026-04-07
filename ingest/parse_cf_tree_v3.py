import re
import json
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


# =========================
# UTILITÁRIOS
# =========================

ROMAN_RE = r"[IVXLCDM]+"
LETTER_RE = r"[a-z]"
ORDINAL_RE = r"\d+[ºo°]?"
PLAIN_INT_RE = r"\d+"


def strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_line(text: str) -> str:
    return normalize_spaces(text.replace("\u00a0", " "))


def roman_to_int(roman: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(roman.upper()):
        val = values.get(ch, 0)
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total


# =========================
# MODELO DA ÁRVORE
# =========================

@dataclass
class Node:
    node_type: str
    label: str
    number_raw: Optional[str] = None
    number_norm: Optional[str] = None
    title: Optional[str] = None
    text: str = ""
    line_start: int = 0
    children: List["Node"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": self.node_type,
            "label": self.label,
            "number_raw": self.number_raw,
            "number_norm": self.number_norm,
            "title": self.title,
            "text": self.text.strip(),
            "line_start": self.line_start,
            "children": [child.to_dict() for child in self.children],
        }


# =========================
# REGRAS HIERÁRQUICAS
# =========================

RANK = {
    "preambulo": 0,
    "titulo": 1,
    "capitulo": 2,
    "secao": 3,
    "subsecao": 4,
    "artigo": 5,
    "paragrafo": 6,
    "inciso": 7,
    "alinea": 8,
    "item": 9,
    "texto_livre": 10,
}

VALID_PARENTS = {
    "preambulo": {"root"},
    "titulo": {"root", "preambulo"},
    "capitulo": {"titulo", "subsecao", "secao"},
    "secao": {"titulo", "capitulo", "subsecao"},
    "subsecao": {"secao", "capitulo", "titulo"},
    "artigo": {"titulo", "capitulo", "secao", "subsecao", "root"},
    "paragrafo": {"artigo"},
    "inciso": {"artigo", "paragrafo"},
    "alinea": {"inciso", "paragrafo"},
    "item": {"alinea", "inciso", "paragrafo"},
    "texto_livre": {
        "root", "preambulo", "titulo", "capitulo", "secao", "subsecao",
        "artigo", "paragrafo", "inciso", "alinea", "item"
    },
}


# =========================
# PADRÕES DE DETECÇÃO
# =========================

PATTERNS = [
    (
        "preambulo",
        re.compile(r"^\s*PRE[ÂA]MBULO\s*$", re.IGNORECASE),
    ),
    (
        "titulo",
        re.compile(
            rf"^\s*T[IÍ]TULO\s+({ROMAN_RE})\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "capitulo",
        re.compile(
            rf"^\s*CAP[IÍ]TULO\s+({ROMAN_RE})\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "secao",
        re.compile(
            rf"^\s*SE[CÇ][AÃ]O\s+({ROMAN_RE})\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "subsecao",
        re.compile(
            rf"^\s*SUBSE[CÇ][AÃ]O\s+({ROMAN_RE})\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "artigo",
        re.compile(
            rf"^\s*Art\.?\s*({PLAIN_INT_RE})(?:[ºo°])?\s*[–\-—.]?\s*(.*)$",
            re.IGNORECASE,
        ),
    ),
    (
        "paragrafo_unico",
        re.compile(
            r"^\s*Par[aá]grafo\s+[uú]nico\s*[–\-—.]?\s*(.*)$",
            re.IGNORECASE,
        ),
    ),
    (
        "paragrafo",
        re.compile(
            rf"^\s*§\s*({PLAIN_INT_RE})(?:[ºo°])?\s*[–\-—.]?\s*(.*)$",
            re.IGNORECASE,
        ),
    ),
    (
        "inciso",
        re.compile(
            rf"^\s*({ROMAN_RE})\s*[-–—]\s*(.*)$",
            re.IGNORECASE,
        ),
    ),
    (
        "alinea",
        re.compile(
            rf"^\s*({LETTER_RE})\)\s*(.*)$",
            re.IGNORECASE,
        ),
    ),
    (
        "item",
        re.compile(
            rf"^\s*({PLAIN_INT_RE})\.\s*(.*)$",
            re.IGNORECASE,
        ),
    ),
]


# =========================
# CLASSIFICAÇÃO DE LINHAS
# =========================

def classify_line(line: str) -> Dict[str, Any]:
    raw = line.rstrip("\n")
    norm = normalize_line(raw)

    if not norm:
        return {"type": "blank", "raw": raw, "text": ""}

    for node_type, pattern in PATTERNS:
        match = pattern.match(norm)
        if not match:
            continue

        if node_type == "preambulo":
            return {
                "type": "preambulo",
                "raw": raw,
                "text": "",
                "label": "PREÂMBULO",
                "number_raw": None,
                "number_norm": None,
            }

        if node_type in {"titulo", "capitulo", "secao", "subsecao"}:
            roman = match.group(1).upper()
            return {
                "type": node_type,
                "raw": raw,
                "text": "",
                "label": norm,
                "number_raw": roman,
                "number_norm": str(roman_to_int(roman)),
            }

        if node_type == "artigo":
            number = match.group(1)
            trailing = match.group(2).strip()
            return {
                "type": "artigo",
                "raw": raw,
                "text": trailing,
                "label": f"Art. {number}",
                "number_raw": number,
                "number_norm": str(int(number)),
            }

        if node_type == "paragrafo_unico":
            trailing = match.group(1).strip()
            return {
                "type": "paragrafo",
                "raw": raw,
                "text": trailing,
                "label": "Parágrafo único",
                "number_raw": "único",
                "number_norm": "unico",
            }

        if node_type == "paragrafo":
            number = match.group(1)
            trailing = match.group(2).strip()
            return {
                "type": "paragrafo",
                "raw": raw,
                "text": trailing,
                "label": f"§ {number}",
                "number_raw": number,
                "number_norm": str(int(number)),
            }

        if node_type == "inciso":
            roman = match.group(1).upper()
            trailing = match.group(2).strip()
            return {
                "type": "inciso",
                "raw": raw,
                "text": trailing,
                "label": roman,
                "number_raw": roman,
                "number_norm": str(roman_to_int(roman)),
            }

        if node_type == "alinea":
            letter = match.group(1).lower()
            trailing = match.group(2).strip()
            return {
                "type": "alinea",
                "raw": raw,
                "text": trailing,
                "label": f"{letter})",
                "number_raw": letter,
                "number_norm": letter,
            }

        if node_type == "item":
            number = match.group(1)
            trailing = match.group(2).strip()
            return {
                "type": "item",
                "raw": raw,
                "text": trailing,
                "label": f"{number}.",
                "number_raw": number,
                "number_norm": str(int(number)),
            }

    return {"type": "texto_livre", "raw": raw, "text": norm}


# =========================
# MONTAGEM DA ÁRVORE
# =========================

def find_parent(stack, node_type):
    valid = VALID_PARENTS[node_type]
    for idx in range(len(stack) - 1, -1, -1):
        if stack[idx].node_type in valid:
            return idx
    return 0


def attach_text_to_current(stack, text):
    if not text:
        return
    current = stack[-1]
    if current.node_type in {"titulo", "capitulo", "secao", "subsecao"} and not current.title:
        if len(text) < 180:
            current.title = text
            return
    if current.text:
        current.text += "\n" + text
    else:
        current.text = text


def parse_constitution_tree(text):
    root = Node(node_type="root", label="ROOT")
    stack = [root]
    lines = text.splitlines()

    for line_no, line in enumerate(lines, start=1):
        info = classify_line(line)

        if info["type"] == "blank":
            continue

        if info["type"] == "texto_livre":
            attach_text_to_current(stack, info["text"])
            continue

        node = Node(
            node_type=info["type"],
            label=info["label"],
            number_raw=info.get("number_raw"),
            number_norm=info.get("number_norm"),
            text=info.get("text", ""),
            line_start=line_no,
        )

        parent_idx = find_parent(stack, node.node_type)
        parent = stack[parent_idx]
        parent.children.append(node)

        stack = stack[:parent_idx + 1]
        stack.append(node)

    return root


# =========================
# FLATTEN
# =========================

def flatten_tree(node, path=None):
    path = path or []
    current_path = path + [node.label] if node.node_type != "root" else path

    rows = []
    if node.node_type != "root":
        rows.append({
            "node_type": node.node_type,
            "label": node.label,
            "number_raw": node.number_raw,
            "number_norm": node.number_norm,
            "title": node.title,
            "text": node.text.strip(),
            "line_start": node.line_start,
            "path": " > ".join(current_path),
        })

    for child in node.children:
        rows.extend(flatten_tree(child, current_path))

    return rows


# =========================
# MAIN: Parse CF from Planalto HTML
# =========================

if __name__ == "__main__":
    import os

    ingest_dir = os.path.join("C:", os.sep, "projetos", "icons", "ingest")

    # Read HTML with latin1
    html_path = os.path.join(ingest_dir, "cf_planalto.html")
    with open(html_path, "r", encoding="latin1") as f:
        html = f.read()

    # Extract paragraphs from HTML (join multi-line <p> blocks)
    p_regex = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)
    tag_regex = re.compile(r"<[^>]+>")

    paragraphs = []
    for match in p_regex.finditer(html):
        text = tag_regex.sub("", match.group(1))
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = normalize_spaces(text)
        if text:
            paragraphs.append(text)

    # Join into single text with newlines
    full_text = "\n".join(paragraphs)

    print(f"Parágrafos extraídos do HTML: {len(paragraphs)}")
    print(f"Caracteres totais: {len(full_text)}")

    # Parse tree
    tree = parse_constitution_tree(full_text)

    # Flatten
    rows = flatten_tree(tree)

    # Stats
    type_count = {}
    for r in rows:
        t = r["node_type"]
        type_count[t] = type_count.get(t, 0) + 1

    print(f"\nTotal de nós: {len(rows)}")
    print("\nPor tipo:")
    for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
        print(f"  {c:6d}  {t}")

    # Check article completeness
    artigos = [r for r in rows if r["node_type"] == "artigo"]
    art_nums = sorted(set(int(a["number_norm"]) for a in artigos))
    print(f"\nArtigos encontrados: {len(artigos)}")
    if art_nums:
        print(f"Range: {art_nums[0]} a {art_nums[-1]}")
        gaps = [i for i in range(1, art_nums[-1] + 1) if i not in art_nums]
        if gaps:
            print(f"Artigos faltantes ({len(gaps)}): {gaps[:20]}{'...' if len(gaps) > 20 else ''}")
        else:
            print("Nenhum artigo faltante!")

    # Show sample
    print("\n=== AMOSTRA (primeiros 30 nós) ===")
    for r in rows[:30]:
        depth = {"preambulo": 0, "titulo": 0, "capitulo": 1, "secao": 2, "subsecao": 3,
                 "artigo": 4, "paragrafo": 5, "inciso": 5, "alinea": 6, "item": 7}.get(r["node_type"], 0)
        indent = "  " * depth
        title_str = f' "{r["title"]}"' if r.get("title") else ""
        text_preview = r["text"][:60] if r["text"] else ""
        print(f'{indent}[{r["node_type"]} {r.get("number_raw", "")}]{title_str} {text_preview}')

    # Save JSON
    json_path = os.path.join(ingest_dir, "13_cf_arvore.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tree.to_dict(), f, ensure_ascii=False, indent=2)

    # Save TSV for Excel
    tsv_path = os.path.join(ingest_dir, "13_cf_arvore_normativa.csv")
    with open(tsv_path, "w", encoding="utf-8-sig") as f:
        f.write("index\ttipo\tnumero\tlabel\ttitle\ttexto\tpath\tline_start\n")
        for i, r in enumerate(rows, 1):
            text_clean = r["text"][:400].replace("\t", " ").replace("\n", " ")
            title_clean = (r.get("title") or "").replace("\t", " ")
            f.write(f'{i}\t{r["node_type"]}\t{r.get("number_raw", "")}\t{r["label"]}\t{title_clean}\t{text_clean}\t{r["path"]}\t{r["line_start"]}\n')

    print(f"\nSalvo: {json_path}")
    print(f"Salvo: {tsv_path}")
