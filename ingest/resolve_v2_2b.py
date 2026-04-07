import csv
import re
import hashlib
import unicodedata
from pathlib import Path
from typing import Dict, List
from collections import Counter

def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\u00a0", " ")).strip()

def strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", text or "") if unicodedata.category(ch) != "Mn")

def normalize_key(text: str) -> str:
    text = normalize_spaces(text)
    text = strip_accents(text).lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", text).strip()

def safe_text(row, *keys):
    for k in keys:
        v = row.get(k, "")
        if v: return v
    return ""

def build_hash(*parts):
    payload = "||".join(normalize_spaces(p) for p in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def read_tsv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def write_tsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

RE_PROCESS = re.compile(r"\b(ADI|ADC|ADO|ADPF|ARE|RE|RHC|HC|MS|Pet|Inq|Ext|Rcl|REsp|AgR|AI|SL|SS|STA)\s+([\d\.\-]+)", re.IGNORECASE)
RE_RELATOR = re.compile(r"rel\.\s*min\.\s*([^,\]\.;]+)", re.IGNORECASE)
RE_DJE = re.compile(r"DJE\s+de\s+([\d\u00bao\u00b0\.\-\/]+)", re.IGNORECASE)
RE_J = re.compile(r"\bj\.\s*([\d\u00bao\u00b0\.\-\/]+)", re.IGNORECASE)
RE_TEMA = re.compile(r"\bTema\s+([\d\.\-]+)", re.IGNORECASE)
RE_SUMULA_VINC = re.compile(r"\bS[u\u00fa]mula\s+Vinculante\s+(\d+)", re.IGNORECASE)

def normalize_process_number(n):
    return re.sub(r"[^\d]", "", n or "")

def extract_case_metadata(text):
    s = normalize_spaces(text)
    out = {"process_class":"","process_number":"","relator":"","julgamento_data":"","dje_data":"","tema_rg":"","sumula_number":""}
    m = RE_PROCESS.search(s)
    if m: out["process_class"] = m.group(1).upper(); out["process_number"] = m.group(2)
    m = RE_RELATOR.search(s)
    if m: out["relator"] = normalize_spaces(m.group(1))
    m = RE_J.search(s)
    if m: out["julgamento_data"] = normalize_spaces(m.group(1))
    m = RE_DJE.search(s)
    if m: out["dje_data"] = normalize_spaces(m.group(1))
    m = RE_TEMA.search(s)
    if m: out["tema_rg"] = normalize_spaces(m.group(1))
    m = RE_SUMULA_VINC.search(s)
    if m: out["sumula_number"] = normalize_spaces(m.group(1))
    return out

def build_process_key(pc, pn, sn=""):
    pc = (pc or "").upper().strip()
    if pc:
        n = normalize_process_number(pn)
        if n: return f"{pc}_{n}"
    if sn: return f"SUMULA_VINCULANTE_{normalize_process_number(sn)}"
    return ""

def classify_decision_unit_type(editorial_marker, editorial_label, metadata_text, process_class, tema_rg, sumula_number):
    marker = normalize_key(editorial_marker or editorial_label)
    meta = normalize_key(metadata_text)
    if sumula_number or "sumula vinculante" in meta or "sumula vinculante" in marker:
        return "sumula_vinculante"
    if tema_rg or "repercussao geral" in marker:
        return "repercussao_geral"
    if "julgados correlatos" in marker or "julgado correlato" in marker:
        return "julgado_correlato"
    if "controle concentrado" in marker:
        if process_class in {"ADI","ADC","ADO","ADPF"}: return "julgado_principal"
        return "controle_concentrado"
    if process_class: return "julgado_principal"
    return "comentario_editorial"

def resolve_decision_blocks(rows):
    resolved = []
    for row in rows:
        block_text = safe_text(row, "block_text", "text")
        metadata_text = row.get("metadata_text", "")
        meta_source = "\n".join([block_text, metadata_text]).strip()
        meta = extract_case_metadata(meta_source)

        pc = row.get("process_class","") or meta["process_class"]
        pn = row.get("process_number","") or meta["process_number"]
        rel = row.get("relator","") or meta["relator"]
        jd = row.get("julgamento_data","") or meta["julgamento_data"]
        dd = row.get("dje_data","") or meta["dje_data"]
        tr = row.get("tema_rg","") or row.get("tema","") or meta["tema_rg"]
        sn = meta["sumula_number"]

        em = row.get("editorial_marker","")
        el = row.get("editorial_label","")
        pk = build_process_key(pc, pn, sn)
        dut = classify_decision_unit_type(em, el, metadata_text, pc, tr, sn)

        anchor_slug = row.get("anchor_slug","")
        bh = build_hash(anchor_slug, em, el, block_text, metadata_text, pk, rel, jd)

        resolved.append({
            "block_id": row.get("block_id",""),
            "paragraph_start": row.get("paragraph_start",""),
            "paragraph_end": row.get("paragraph_end",""),
            "anchor_slug": anchor_slug,
            "anchor_label": row.get("anchor_label",""),
            "anchor_node_type": row.get("anchor_node_type",""),
            "anchor_quality": row.get("anchor_quality",""),
            "anchor_confidence": row.get("anchor_confidence",""),
            "matched_variant": row.get("matched_variant",""),
            "variant_origin": row.get("variant_origin",""),
            "match_priority": row.get("match_priority",""),
            "context_relation": row.get("context_relation",""),
            "namespace": row.get("anchor_namespace","") or row.get("namespace",""),
            "editorial_marker": em,
            "editorial_label": el,
            "decision_unit_type": dut,
            "block_text": block_text,
            "metadata_text": metadata_text,
            "process_class": pc,
            "process_number": pn,
            "process_key": pk,
            "relator": rel,
            "julgamento_data": jd,
            "dje_data": dd,
            "tema_rg": tr,
            "sumula_number": sn,
            "raw_signature": f"{em} | {pc} {pn} | rel. {rel} | j. {jd}".strip(" |"),
            "block_hash": bh,
        })
    return resolved

def main():
    base = Path(r"C:\projetos\icons\ingest\saida_parser")

    # Try matched v2.1 first, then regular commentary_blocks
    input_path = base / "commentary_blocks_matched_v2_1.tsv"
    if not input_path.exists():
        input_path = base / "commentary_blocks.tsv"

    output_path = base / "decision_blocks_resolved.tsv"

    print(f"Input: {input_path}")
    rows = read_tsv(input_path)
    print(f"Blocos lidos: {len(rows)}")

    resolved = resolve_decision_blocks(rows)
    write_tsv(output_path, resolved)

    # Stats
    total = len(resolved)
    dut = Counter(r["decision_unit_type"] for r in resolved)
    qual = Counter(r["anchor_quality"] for r in resolved)
    with_pk = sum(1 for r in resolved if r["process_key"])
    with_rel = sum(1 for r in resolved if r["relator"])
    with_tema = sum(1 for r in resolved if r["tema_rg"])
    pks = len(set(r["process_key"] for r in resolved if r["process_key"]))
    rels = Counter(r["relator"] for r in resolved if r["relator"])
    cls = Counter(r["process_class"] for r in resolved if r["process_class"])

    print(f"\n{'='*70}")
    print(f"  DECISION BLOCKS RESOLVED v2.2-b")
    print(f"{'='*70}")
    print(f"  Total: {total}")
    print(f"\n  Por decision_unit_type:")
    for t, n in dut.most_common():
        print(f"    {t:30s} {n:5d} ({n/total*100:.1f}%)")
    print(f"\n  Por anchor_quality:")
    for q, n in qual.most_common():
        print(f"    {q or 'vazio':15s} {n:5d}")
    print(f"\n  Com process_key: {with_pk} ({with_pk/total*100:.1f}%)")
    print(f"  Com relator: {with_rel} ({with_rel/total*100:.1f}%)")
    print(f"  Com tema_rg: {with_tema}")
    print(f"  Process keys unicos: {pks}")
    print(f"  Relatores unicos: {len(rels)}")
    print(f"\n  Top 10 relatores:")
    for r, n in rels.most_common(10):
        print(f"    {r:30s} {n:5d}")
    print(f"\n  Top 10 classes:")
    for c, n in cls.most_common(10):
        print(f"    {c:10s} {n:5d}")
    print(f"\n  Salvo: {output_path}")
    print(f"  Tamanho: {output_path.stat().st_size/1024/1024:.1f} MB")

if __name__ == "__main__":
    main()
