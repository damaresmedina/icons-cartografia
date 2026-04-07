import re
import csv
import json
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from docx import Document


# =========================================================
# UTILITÁRIOS
# =========================================================

ROMAN_RE = r"[IVXLCDM]+"
INT_RE = r"\d+"
LETTER_RE = r"[a-z]"

EDITORIAL_MARKERS = {
    "controle concentrado de constitucionalidade": "controle_concentrado",
    "repercussão geral": "repercussao_geral",
    "repercussao geral": "repercussao_geral",
    "julgados correlatos": "julgados_correlatos",
    "súmula vinculante": "sumula_vinculante",
    "sumula vinculante": "sumula_vinculante",
}


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def normalize_key(text: str) -> str:
    return strip_accents(normalize_spaces(text)).lower()


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


def safe_slug(text: str) -> str:
    text = normalize_key(text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def write_tsv(path: Path, rows: List[Dict[str, Any]]) -> None:
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
# MODELOS
# =========================================================

@dataclass
class NormNode:
    node_type: str
    label: str
    slug: str
    parent_slug: Optional[str]
    number_raw: Optional[str] = None
    number_norm: Optional[str] = None
    title: Optional[str] = None
    text: str = ""
    style_name: Optional[str] = None
    paragraph_index: int = 0
    children: List["NormNode"] = field(default_factory=list)

    def flat_row(self, path: str) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "parent_slug": self.parent_slug or "",
            "node_type": self.node_type,
            "label": self.label,
            "number_raw": self.number_raw or "",
            "number_norm": self.number_norm or "",
            "title": self.title or "",
            "text": self.text.strip(),
            "style_name": self.style_name or "",
            "paragraph_index": self.paragraph_index,
            "path": path,
        }


@dataclass
class CommentBlock:
    block_id: str
    anchor_slug: str
    anchor_label: str
    editorial_marker: str
    editorial_label: str
    text: str
    metadata_text: str
    process_class: str
    process_number: str
    relator: str
    julgamento_data: str
    dje_data: str
    tema: str
    paragraph_start: int
    paragraph_end: int


# =========================================================
# PADRÕES NORMATIVOS
# =========================================================

RE_PREAMBULO = re.compile(r"^\s*PREÂMBULO\s*$", re.IGNORECASE)
RE_TITULO = re.compile(rf"^\s*T[IÍ]TULO\s+({ROMAN_RE})\s*$", re.IGNORECASE)
RE_CAPITULO = re.compile(rf"^\s*CAP[IÍ]TULO\s+({ROMAN_RE})\s*$", re.IGNORECASE)
RE_SECAO = re.compile(rf"^\s*SE[CÇ][AÃ]O\s+({ROMAN_RE})\s*$", re.IGNORECASE)
RE_SUBSECAO = re.compile(rf"^\s*SUBSE[CÇ][AÃ]O\s+({ROMAN_RE})\s*$", re.IGNORECASE)

RE_ARTIGO = re.compile(
    rf"^\s*Art\.\s*({INT_RE})(?:[ºo°])?\s*[–\-—]?\s*(.*)$",
    re.IGNORECASE,
)
RE_PAR_UNICO = re.compile(r"^\s*Par[aá]grafo\s+[uú]nico\s*[–\-—]?\s*(.*)$", re.IGNORECASE)
RE_PARAGRAFO = re.compile(
    rf"^\s*§\s*({INT_RE})(?:[ºo°])?\s*[–\-—]?\s*(.*)$",
    re.IGNORECASE,
)
RE_INCISO = re.compile(rf"^\s*({ROMAN_RE})\s*[-–—]\s*(.*)$", re.IGNORECASE)
RE_ALINEA = re.compile(rf"^\s*({LETTER_RE})\)\s*(.*)$", re.IGNORECASE)
RE_ITEM = re.compile(rf"^\s*({INT_RE})\.\s*(.*)$", re.IGNORECASE)


# =========================================================
# LEITURA DO DOCX
# =========================================================

def read_docx_paragraphs(path: Path) -> List[Dict[str, Any]]:
    doc = Document(str(path))
    paragraphs = []
    for idx, p in enumerate(doc.paragraphs, start=1):
        text = normalize_spaces(p.text)
        style_name = p.style.name if p.style else ""
        if not text:
            continue
        paragraphs.append({
            "paragraph_index": idx,
            "text": text,
            "style_name": style_name,
        })
    return paragraphs


# =========================================================
# PARSER DA ÁRVORE CANÔNICA DA CF
# =========================================================

RANK = {
    "root": -1,
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
}


VALID_PARENTS = {
    "preambulo": {"root"},
    "titulo": {"root", "preambulo"},
    "capitulo": {"titulo"},
    "secao": {"capitulo", "titulo"},
    "subsecao": {"secao", "capitulo", "titulo"},
    "artigo": {"subsecao", "secao", "capitulo", "titulo", "root"},
    "paragrafo": {"artigo"},
    "inciso": {"artigo", "paragrafo"},
    "alinea": {"inciso", "paragrafo"},
    "item": {"alinea", "inciso", "paragrafo"},
}


def classify_normative_paragraph(text: str) -> Dict[str, Any]:
    if RE_PREAMBULO.match(text):
        return {"type": "preambulo", "label": "PREÂMBULO"}

    m = RE_TITULO.match(text)
    if m:
        roman = m.group(1).upper()
        return {"type": "titulo", "label": f"TÍTULO {roman}", "number_raw": roman, "number_norm": str(roman_to_int(roman))}

    m = RE_CAPITULO.match(text)
    if m:
        roman = m.group(1).upper()
        return {"type": "capitulo", "label": f"CAPÍTULO {roman}", "number_raw": roman, "number_norm": str(roman_to_int(roman))}

    m = RE_SECAO.match(text)
    if m:
        roman = m.group(1).upper()
        return {"type": "secao", "label": f"SEÇÃO {roman}", "number_raw": roman, "number_norm": str(roman_to_int(roman))}

    m = RE_SUBSECAO.match(text)
    if m:
        roman = m.group(1).upper()
        return {"type": "subsecao", "label": f"SUBSEÇÃO {roman}", "number_raw": roman, "number_norm": str(roman_to_int(roman))}

    m = RE_ARTIGO.match(text)
    if m:
        n = m.group(1)
        trailing = m.group(2).strip()
        return {"type": "artigo", "label": f"Art. {n}", "number_raw": n, "number_norm": str(int(n)), "text": trailing}

    m = RE_PAR_UNICO.match(text)
    if m:
        return {"type": "paragrafo", "label": "Parágrafo único", "number_raw": "único", "number_norm": "unico", "text": m.group(1).strip()}

    m = RE_PARAGRAFO.match(text)
    if m:
        n = m.group(1)
        return {"type": "paragrafo", "label": f"§ {n}", "number_raw": n, "number_norm": str(int(n)), "text": m.group(2).strip()}

    m = RE_INCISO.match(text)
    if m:
        roman = m.group(1).upper()
        return {"type": "inciso", "label": roman, "number_raw": roman, "number_norm": str(roman_to_int(roman)), "text": m.group(2).strip()}

    m = RE_ALINEA.match(text)
    if m:
        letter = m.group(1).lower()
        return {"type": "alinea", "label": f"{letter})", "number_raw": letter, "number_norm": letter, "text": m.group(2).strip()}

    m = RE_ITEM.match(text)
    if m:
        n = m.group(1)
        return {"type": "item", "label": f"{n}.", "number_raw": n, "number_norm": str(int(n)), "text": m.group(2).strip()}

    return {"type": "texto_livre", "text": text}


def find_parent(stack: List[NormNode], node_type: str) -> int:
    allowed = VALID_PARENTS[node_type]
    for i in range(len(stack) - 1, -1, -1):
        if stack[i].node_type in allowed:
            return i
    return 0


def build_cf_tree(cf_paragraphs: List[Dict[str, Any]]) -> NormNode:
    root = NormNode(node_type="root", label="ROOT", slug="cf-1988-root", parent_slug=None)
    stack = [root]

    for p in cf_paragraphs:
        text = p["text"]
        style_name = p["style_name"]
        paragraph_index = p["paragraph_index"]

        info = classify_normative_paragraph(text)

        if info["type"] == "texto_livre":
            current = stack[-1]
            if current.node_type in {"titulo", "capitulo", "secao", "subsecao"} and not current.title:
                if len(text) <= 200:
                    current.title = text
                else:
                    current.text = (current.text + "\n" + text).strip() if current.text else text
            else:
                current.text = (current.text + "\n" + text).strip() if current.text else text
            continue

        node_type = info["type"]
        label = info["label"]
        number_raw = info.get("number_raw")
        number_norm = info.get("number_norm")
        node_text = info.get("text", "")

        parent_idx = find_parent(stack, node_type)
        parent = stack[parent_idx]

        if node_type == "preambulo":
            slug_parts = ["cf-1988", "preambulo"]
        elif node_type == "titulo":
            slug_parts = ["cf-1988", f"tit-{number_norm}"]
        elif node_type == "capitulo":
            slug_parts = [parent.slug, f"cap-{number_norm}"]
        elif node_type == "secao":
            slug_parts = [parent.slug, f"sec-{number_norm}"]
        elif node_type == "subsecao":
            slug_parts = [parent.slug, f"subsec-{number_norm}"]
        elif node_type == "artigo":
            slug_parts = ["cf-1988", f"art-{number_norm}"]
        elif node_type == "paragrafo":
            slug_parts = [parent.slug, f"par-{number_norm}"]
        elif node_type == "inciso":
            slug_parts = [parent.slug, f"inc-{number_norm}"]
        elif node_type == "alinea":
            slug_parts = [parent.slug, f"ali-{number_norm}"]
        elif node_type == "item":
            slug_parts = [parent.slug, f"item-{number_norm}"]
        else:
            slug_parts = [parent.slug, safe_slug(label)]

        slug = "-".join(slug_parts).replace("--", "-")

        node = NormNode(
            node_type=node_type, label=label, slug=slug,
            parent_slug=parent.slug if parent.node_type != "root" else None,
            number_raw=number_raw, number_norm=number_norm,
            text=node_text, style_name=style_name, paragraph_index=paragraph_index,
        )
        parent.children.append(node)
        stack = stack[:parent_idx + 1]
        stack.append(node)

    return root


def flatten_norm_tree(node: NormNode, path: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    path = path or []
    current_path = path + ([node.label] if node.node_type != "root" else [])
    rows = []
    if node.node_type != "root":
        rows.append(node.flat_row(" > ".join(current_path)))
    for child in node.children:
        rows.extend(flatten_norm_tree(child, current_path))
    return rows


def build_anchor_index(norm_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    anchors = {}
    for row in norm_rows:
        node_type = row["node_type"]
        label = row["label"]
        slug = row["slug"]
        candidates = [label]

        if node_type == "artigo":
            number = row["number_norm"]
            candidates.extend([f"Art. {number}", f"Art {number}", f"Art. {number}o", f"Art. {number}"])
        elif node_type == "paragrafo":
            if row["number_norm"] == "unico":
                candidates.extend(["Parágrafo único", "Paragrafo unico"])
            else:
                number = row["number_norm"]
                candidates.extend([f"§ {number}", f"§ {number}o"])
        elif node_type == "inciso":
            roman = row["number_raw"]
            candidates.extend([f"{roman} -", f"{roman} –", f"{roman} —"])
        elif node_type == "alinea":
            letter = row["number_norm"]
            candidates.append(f"{letter})")

        for c in candidates:
            anchors[normalize_key(c)] = {"slug": slug, "label": label, "node_type": node_type}

    return anchors


# =========================================================
# PARSER DO DOCUMENTO COMENTADO
# =========================================================

RE_BRACKET_METADATA = re.compile(r"^\s*\[(.+)\]\s*$")
RE_PROCESS = re.compile(
    r"\b(ADI|ADC|ADO|ADPF|ARE|RE|RHC|HC|MS|Pet|Inq|Ext|Rcl|REsp|AgR|AI|SL|SS|STA)\s+([\d\.\-]+)",
    re.IGNORECASE,
)
RE_RELATOR = re.compile(r"rel\.\s*min\.\s*([^,\]]+)", re.IGNORECASE)
RE_JULG = re.compile(r"j\.\s*([\dºo°\.\-\/]+)", re.IGNORECASE)
RE_DJE = re.compile(r"DJE\s+de\s+([\dºo°\.\-\/]+)", re.IGNORECASE)
RE_TEMA = re.compile(r"Tema\s+([\d\.\-]+)", re.IGNORECASE)


RE_ART_ANCORA = re.compile(r'^Art\.?\s*(\d+)[º°]?[\s\.\,\-\u2013\u2014]')
RE_PAR_ANCORA = re.compile(r'^\u00a7?\s*§\s*(\d+|[uú]nico)[º°]?[\s\.\,\-\u2013\u2014]', re.IGNORECASE)
RE_PAR_UNICO_ANCORA = re.compile(r'^Par[aá]grafo\s+[uú]nico', re.IGNORECASE)
RE_INC_ANCORA = re.compile(rf'^({ROMAN_RE})\s*[-\u2013\u2014]', re.IGNORECASE)
RE_ALI_ANCORA = re.compile(rf'^({LETTER_RE})\)\s')

def classify_commentary_paragraph(text: str, anchor_index: Dict[str, Dict[str, Any]], valid_art_nums: set = None) -> Tuple[str, Optional[Dict[str, Any]]]:
    key = normalize_key(text)
    t = text.strip()

    # A — Art. N (cotejado com artigos válidos da CF)
    m_art = RE_ART_ANCORA.match(t)
    if m_art:
        art_num = int(m_art.group(1))
        if valid_art_nums and art_num in valid_art_nums:
            slug = f"cf-1988-art-{art_num}"
            if slug in {a["slug"] for a in anchor_index.values()}:
                return "A", {"slug": slug, "label": f"Art. {art_num}", "node_type": "artigo"}

    # A — § / Parágrafo único / Inciso / Alínea (via anchor_index)
    for candidate, anchor in anchor_index.items():
        if anchor["node_type"] in ("paragrafo", "inciso", "alinea") and key.startswith(candidate):
            return "A", anchor

    # B — editorial
    if key in EDITORIAL_MARKERS:
        return "B", {"editorial_code": EDITORIAL_MARKERS[key], "editorial_label": text}

    # D — metadado entre colchetes
    if RE_BRACKET_METADATA.match(text):
        return "D", None

    # C — texto
    return "C", None


def extract_case_metadata(text: str) -> Dict[str, str]:
    meta = {"process_class": "", "process_number": "", "relator": "", "julgamento_data": "", "dje_data": "", "tema": ""}
    m = RE_PROCESS.search(text)
    if m:
        meta["process_class"] = m.group(1).upper()
        meta["process_number"] = m.group(2)
    m = RE_RELATOR.search(text)
    if m:
        meta["relator"] = normalize_spaces(m.group(1))
    m = RE_JULG.search(text)
    if m:
        meta["julgamento_data"] = normalize_spaces(m.group(1))
    m = RE_DJE.search(text)
    if m:
        meta["dje_data"] = normalize_spaces(m.group(1))
    m = RE_TEMA.search(text)
    if m:
        meta["tema"] = normalize_spaces(m.group(1))
    return meta


def parse_commentary_blocks(
    commentary_paragraphs: List[Dict[str, Any]],
    anchor_index: Dict[str, Dict[str, Any]],
    valid_art_nums: set = None,
) -> List[CommentBlock]:
    current_anchor = {"slug": "", "label": ""}
    current_editorial_code = ""
    current_editorial_label = ""
    current_text_parts: List[str] = []
    current_metadata_parts: List[str] = []
    block_start = None
    block_counter = 0
    blocks: List[CommentBlock] = []

    def flush(paragraph_end: int) -> None:
        nonlocal current_text_parts, current_metadata_parts, block_start, block_counter
        text = "\n".join(current_text_parts).strip()
        metadata_text = "\n".join(current_metadata_parts).strip()
        if not text and not metadata_text:
            return
        if not current_anchor["slug"]:
            current_text_parts = []
            current_metadata_parts = []
            block_start = None
            return
        merged = (text + "\n" + metadata_text).strip()
        meta = extract_case_metadata(merged)
        block_counter += 1
        blocks.append(CommentBlock(
            block_id=f"blk-{block_counter:06d}",
            anchor_slug=current_anchor["slug"],
            anchor_label=current_anchor["label"],
            editorial_marker=current_editorial_code,
            editorial_label=current_editorial_label,
            text=text, metadata_text=metadata_text,
            process_class=meta["process_class"],
            process_number=meta["process_number"],
            relator=meta["relator"],
            julgamento_data=meta["julgamento_data"],
            dje_data=meta["dje_data"],
            tema=meta["tema"],
            paragraph_start=block_start or paragraph_end,
            paragraph_end=paragraph_end,
        ))
        current_text_parts = []
        current_metadata_parts = []
        block_start = None

    for p in commentary_paragraphs:
        idx = p["paragraph_index"]
        text = p["text"]
        cls, info = classify_commentary_paragraph(text, anchor_index, valid_art_nums)

        if cls == "A":
            flush(idx - 1)
            current_anchor = {"slug": info["slug"], "label": info["label"]}
            current_editorial_code = ""
            current_editorial_label = ""
        elif cls == "B":
            flush(idx - 1)
            current_editorial_code = info["editorial_code"]
            current_editorial_label = info["editorial_label"]
        elif cls == "C":
            if block_start is None:
                block_start = idx
            current_text_parts.append(text)
        elif cls == "D":
            if block_start is None:
                block_start = idx
            current_metadata_parts.append(text)
            flush(idx)

    flush(commentary_paragraphs[-1]["paragraph_index"] if commentary_paragraphs else 0)
    return blocks


# =========================================================
# EXPORTS
# =========================================================

def export_norm_tree(root: NormNode, output_dir: Path) -> List[Dict[str, Any]]:
    rows = flatten_norm_tree(root)
    write_tsv(output_dir / "norm_tree.tsv", rows)
    return rows


def export_anchor_index(anchor_index: Dict[str, Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    rows = []
    for anchor_text, meta in sorted(anchor_index.items(), key=lambda x: x[0]):
        rows.append({"anchor_text_norm": anchor_text, "slug": meta["slug"], "label": meta["label"], "node_type": meta["node_type"]})
    write_tsv(output_dir / "norm_anchor_index.tsv", rows)
    return rows


def export_commentary_blocks(blocks: List[CommentBlock], output_dir: Path) -> List[Dict[str, Any]]:
    rows = [asdict(b) for b in blocks]
    write_tsv(output_dir / "commentary_blocks.tsv", rows)
    return rows


# =========================================================
# PIPELINE PRINCIPAL
# =========================================================

def run_pipeline(cf_docx_path: str, commentary_docx_path: str, output_dir: str) -> None:
    output = Path(output_dir)

    print("FASE 1 — Arvore canonica da CF...")
    cf_paragraphs = read_docx_paragraphs(Path(cf_docx_path))
    cf_root = build_cf_tree(cf_paragraphs)
    norm_rows = export_norm_tree(cf_root, output)
    print(f"  Nos: {len(norm_rows)}")

    print("\nFASE 2 — Indice de ancoras...")
    anchor_index = build_anchor_index(norm_rows)
    anchor_rows = export_anchor_index(anchor_index, output)
    print(f"  Ancoras: {len(anchor_rows)}")

    # Build valid article numbers from tree
    valid_art_nums = set()
    for row in norm_rows:
        if row["node_type"] == "artigo" and row["number_norm"]:
            valid_art_nums.add(int(row["number_norm"]))
    print(f"  Artigos validos CF: {len(valid_art_nums)}")

    print("\nFASE 3 — Documento comentado...")
    commentary_paragraphs = read_docx_paragraphs(Path(commentary_docx_path))
    print(f"  Paragrafos: {len(commentary_paragraphs)}")
    blocks = parse_commentary_blocks(commentary_paragraphs, anchor_index, valid_art_nums)
    block_rows = export_commentary_blocks(blocks, output)
    print(f"  Blocos: {len(block_rows)}")

    # JSON
    with (output / "norm_tree.json").open("w", encoding="utf-8") as f:
        json.dump({"root": "cf-1988-root", "total_nodes": len(norm_rows)}, f, ensure_ascii=False, indent=2)

    with (output / "commentary_blocks.json").open("w", encoding="utf-8") as f:
        json.dump(block_rows, f, ensure_ascii=False, indent=2)

    # Diagnostico
    from collections import Counter
    arts = set()
    for b in block_rows:
        slug = b.get("anchor_slug", "")
        m = re.match(r"cf-1988-art-(\d+)", slug)
        if m:
            arts.add(int(m.group(1)))

    eds = Counter(b.get("editorial_marker", "") for b in block_rows)
    procs = sum(1 for b in block_rows if b.get("process_class"))

    print(f"\n=== DIAGNOSTICO FINAL ===")
    print(f"  Nos na arvore: {len(norm_rows)}")
    print(f"  Blocos resolvidos: {len(block_rows)}")
    print(f"  Artigos cobertos: {len(arts)}")
    print(f"  Blocos com processo: {procs}")
    print(f"  Por editorial:")
    for ed, n in eds.most_common():
        print(f"    {ed or 'sem_marcador'}: {n}")

    # Art. 5
    art5 = [b for b in block_rows if b.get("anchor_slug", "").startswith("cf-1988-art-5")]
    print(f"\n  Art. 5 blocos: {len(art5)}")
    for b in art5[:3]:
        print(f"    [{b['block_id']}] [{b['anchor_slug']}] [{b['editorial_marker']}]")
        print(f"      texto: {b['text'][:80]}")
        print(f"      meta:  {b['metadata_text'][:80]}")

    print(f"\n  Arquivos em: {output}")


if __name__ == "__main__":
    run_pipeline(
        cf_docx_path=r"C:\projetos\icons\ingest\CF_1988_arvore_completa.docx",
        commentary_docx_path=r"C:\projetos\icons\ingest\cf_comentada.docx",
        output_dir=r"C:\projetos\icons\ingest\saida_parser",
    )
