import os
import re
from collections import Counter

ingest_dir = os.path.join("C:", os.sep, "projetos", "icons", "ingest")

with open(os.path.join(ingest_dir, "01_raw_text.txt"), "r", encoding="utf-8") as f:
    text = f.read()

lines = text.split("\n")
non_empty = [l for l in lines if l.strip()]

print("=" * 70)
print("DIAGNOSTICO COMPLETO")
print("constituicao e o supremo.docx")
print("=" * 70)

print(f"\n1. DIMENSOES")
print(f"   Linhas totais:      {len(lines):,}")
print(f"   Linhas nao-vazias:  {len(non_empty):,}")
print(f"   Caracteres:         {len(text):,}")
print(f"   Palavras (aprox):   {len(text.split()):,}")

# 2. ARTIGOS
art_pattern = re.compile(r"^Art\.\s*(\d+)[^0-9]", re.IGNORECASE)
artigos = []
for i, line in enumerate(lines):
    m = art_pattern.match(line.strip())
    if m:
        artigos.append({"numero": int(m.group(1)), "linha": i + 1})

art_nums = sorted(set(a["numero"] for a in artigos))
print(f"\n2. ARTIGOS")
print(f"   Mencoes a Art.:     {len(artigos)}")
print(f"   Artigos unicos:     {len(art_nums)}")
if art_nums:
    print(f"   Range:              {art_nums[0]} a {art_nums[-1]}")
    gaps = [i for i in range(1, art_nums[-1] + 1) if i not in art_nums]
    print(f"   Faltantes:          {len(gaps)}")
    if gaps:
        print(f"   Quais:              {gaps[:30]}{'...' if len(gaps) > 30 else ''}")

# 3. ESTRUTURA
titulo_pat = re.compile(r"^T[II]TULO\s+([IVXLCDM]+)", re.IGNORECASE)
capitulo_pat = re.compile(r"^CAP[II]TULO\s+([IVXLCDM]+)", re.IGNORECASE)
secao_pat = re.compile(r"^Se[cC][aA]o\s+([IVXLCDM]+)", re.IGNORECASE)

titulos = sum(1 for l in non_empty if titulo_pat.match(l.strip()))
capitulos = sum(1 for l in non_empty if capitulo_pat.match(l.strip()))
secoes = sum(1 for l in non_empty if secao_pat.match(l.strip()))

print(f"\n3. ESTRUTURA HIERARQUICA")
print(f"   Titulos:            {titulos}")
print(f"   Capitulos:          {capitulos}")
print(f"   Secoes:             {secoes}")

# 4. DECISOES (entre colchetes)
bracket_pat = re.compile(r"\[([A-Z]{2,}[^\]]{5,}?)\]")
brackets = bracket_pat.findall(text)

proc_pat = re.compile(r"^(ADI|ADPF|ADC|ADO|RE|ARE|HC|RHC|MS|MI|AP|ACO|Rcl|AI|Pet|SS|SL|IF|Inq|Ext|AC|AgR|ED|MC|QO|SV|PSV|AO|AR|RMS|CR|Rp)\s*[-n.]*\s*([\d.]+(?:[-/]\d+)?)")
rel_pat = re.compile(r"rel\.?\s*(?:p/\s*o?\s*ac\.?\s*)?min\.?\s*([^,\]]+)")
data_pat = re.compile(r"j\.\s*(\d[\d\-]+(?:\s*de\s*\w+\s*de\s*\d+)?)")
orgao_pat = re.compile(r",\s*(P|1.?\s*T|2.?\s*T)\s*[,\]]")
tema_pat = re.compile(r"[Tt]ema\s*(\d+)")
dje_pat = re.compile(r"D[Jj][Ee]?\s*de\s*(\d[\d\-/]+)")

decisoes = []
classes_counter = Counter()
relatores_counter = Counter()
orgaos_counter = Counter()

for b in brackets:
    pm = proc_pat.match(b.strip())
    if pm:
        classe = pm.group(1)
        numero = pm.group(2)
        rel = rel_pat.search(b)
        data = data_pat.search(b)
        orgao = orgao_pat.search(b)
        tema = tema_pat.search(b)
        dje = dje_pat.search(b)

        d = {
            "classe": classe,
            "numero": numero,
            "relator": rel.group(1).strip() if rel else "",
            "data_julgamento": data.group(1).strip() if data else "",
            "orgao": orgao.group(1).strip() if orgao else "",
            "tema_rg": tema.group(1) if tema else "",
            "dje": dje.group(1).strip() if dje else "",
        }
        decisoes.append(d)
        classes_counter[classe] += 1
        if d["relator"]:
            relatores_counter[d["relator"]] += 1
        if d["orgao"]:
            orgaos_counter[d["orgao"]] += 1

seen = set()
unique = []
for d in decisoes:
    key = d["classe"] + " " + d["numero"]
    if key not in seen:
        seen.add(key)
        unique.append(d)

print(f"\n4. DECISOES DO STF (entre colchetes)")
print(f"   Total de mencoes:   {len(decisoes):,}")
print(f"   Decisoes unicas:    {len(unique):,}")
print(f"   Com relator:        {sum(1 for d in unique if d['relator']):,}")
print(f"   Com data:           {sum(1 for d in unique if d['data_julgamento']):,}")
print(f"   Com orgao:          {sum(1 for d in unique if d['orgao']):,}")
print(f"   Com tema RG:        {sum(1 for d in unique if d['tema_rg']):,}")
print(f"   Com DJE:            {sum(1 for d in unique if d['dje']):,}")

print(f"\n   TOP 15 CLASSES:")
for cls, cnt in classes_counter.most_common(15):
    print(f"     {cnt:5d}  {cls}")

print(f"\n   TOP 15 RELATORES:")
for rel, cnt in relatores_counter.most_common(15):
    print(f"     {cnt:5d}  {rel}")

print(f"\n   ORGAOS JULGADORES:")
for org, cnt in orgaos_counter.most_common():
    print(f"     {cnt:5d}  {org}")

# 5. MARCADORES EDITORIAIS
ed_patterns = [
    ("Controle concentrado", re.compile(r"Controle\s+concentrado", re.IGNORECASE)),
    ("Repercussao geral", re.compile(r"Repercuss.o\s+geral", re.IGNORECASE)),
    ("Julgados correlatos", re.compile(r"Julgado.?\s+correlato", re.IGNORECASE)),
    ("Sumula vinculante", re.compile(r"S.mula.?\s+[Vv]inculante", re.IGNORECASE)),
    ("Sumula", re.compile(r"^S.mula.?\s*$", re.IGNORECASE)),
]

ed_counts = Counter()
for line in non_empty:
    l = line.strip()
    for name, pat in ed_patterns:
        if pat.search(l) and len(l) < 100:
            ed_counts[name] += 1

print(f"\n5. MARCADORES EDITORIAIS")
for name, cnt in ed_counts.most_common():
    print(f"   {cnt:5d}  {name}")

# 6. DISPOSITIVOS INFRA-ARTIGO
inc_pat = re.compile(r"^([IVXLCDM]+)\s*[-\u2013\u2014]")
par_pat2 = re.compile(r"^(\u00a7\s*\d+|Par.grafo\s+.nico)", re.IGNORECASE)
ali_pat = re.compile(r"^[a-z]\)")

incisos = sum(1 for l in non_empty if inc_pat.match(l.strip()))
paragrafos = sum(1 for l in non_empty if par_pat2.match(l.strip()))
alineas = sum(1 for l in non_empty if ali_pat.match(l.strip()))

print(f"\n6. DISPOSITIVOS INFRA-ARTIGO")
print(f"   Incisos:            {incisos:,}")
print(f"   Paragrafos:         {paragrafos:,}")
print(f"   Alineas:            {alineas:,}")

# 7. PROPORCAO
norma = 0
decisao = 0
editorial = 0
outro = 0

for line in non_empty:
    l = line.strip()
    if art_pattern.match(l) or inc_pat.match(l) or par_pat2.match(l) or ali_pat.match(l):
        norma += 1
    elif titulo_pat.match(l) or capitulo_pat.match(l) or secao_pat.match(l):
        norma += 1
    elif bracket_pat.search(l):
        decisao += 1
    elif any(pat.search(l) for _, pat in ed_patterns):
        editorial += 1
    else:
        outro += 1

print(f"\n7. PROPORCAO (por linhas)")
print(f"   Normativas:         {norma:,} ({norma/len(non_empty)*100:.1f}%)")
print(f"   Com decisao:        {decisao:,} ({decisao/len(non_empty)*100:.1f}%)")
print(f"   Editoriais:         {editorial:,} ({editorial/len(non_empty)*100:.1f}%)")
print(f"   Outras (texto):     {outro:,} ({outro/len(non_empty)*100:.1f}%)")

# 8. COBERTURA POR ARTIGO
art_positions = []
for i, line in enumerate(lines):
    m = art_pattern.match(line.strip())
    if m:
        art_positions.append({"numero": int(m.group(1)), "linha": i})

art_dec_count = Counter()
for idx, art in enumerate(art_positions):
    start = art["linha"]
    end = art_positions[idx + 1]["linha"] if idx + 1 < len(art_positions) else len(lines)
    block = "\n".join(lines[start:end])
    procs = bracket_pat.findall(block)
    cnt = sum(1 for p in procs if proc_pat.match(p.strip()))
    if cnt > 0:
        art_dec_count[art["numero"]] = cnt

print(f"\n8. COBERTURA DE DECISOES POR ARTIGO")
print(f"   Artigos com decisoes: {len(art_dec_count)} de {len(art_nums)}")
if art_nums:
    print(f"   Cobertura:            {len(art_dec_count)/len(art_nums)*100:.1f}%")
    print(f"   Artigos sem decisao:  {len(art_nums) - len(art_dec_count)}")

print(f"\n   TOP 20 ARTIGOS MAIS LITIGADOS:")
for art, cnt in art_dec_count.most_common(20):
    print(f"     Art. {art:3d}  ->  {cnt:4d} decisoes")

# Artigos sem decisao
arts_sem = sorted(set(art_nums) - set(art_dec_count.keys()))
if arts_sem:
    print(f"\n   ARTIGOS SEM NENHUMA DECISAO ({len(arts_sem)}):")
    print(f"     {arts_sem[:40]}{'...' if len(arts_sem) > 40 else ''}")

# 9. ADCT
adct_start = None
for i, line in enumerate(lines):
    if re.search(r"Ato das Disposi", line, re.IGNORECASE) or re.search(r"^ADCT", line.strip()):
        adct_start = i
        break

print(f"\n9. ADCT")
if adct_start:
    print(f"   Detectado na linha: {adct_start + 1}")
    print(f"   Linhas apos ADCT:   {len(lines) - adct_start}")
else:
    print(f"   Nao detectado explicitamente")

# 10. QUALIDADE
print(f"\n10. QUALIDADE")
encoding_issues = sum(1 for l in non_empty if "\ufffd" in l)
print(f"    Erros de encoding:  {encoding_issues}")
short = sum(1 for l in non_empty if 0 < len(l.strip()) < 3)
print(f"    Linhas < 3 chars:   {short}")
long = sum(1 for l in non_empty if len(l.strip()) > 2000)
print(f"    Linhas > 2000:      {long}")

print(f"\n{'=' * 70}")
print("FIM DO DIAGNOSTICO")
print(f"{'=' * 70}")
