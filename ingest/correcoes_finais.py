import json, os, re
from collections import Counter, defaultdict

OUT = os.path.join("C:", os.sep, "projetos", "icons", "ingest", "saida_parser")

with open(os.path.join(OUT, "commentary_blocks.json"), "r", encoding="utf-8") as f:
    blocks = json.load(f)

# ══════════════════════════════════════════
# CORREÇÃO 1 — Art. 233 é ADCT
# ══════════════════════════════════════════

ADCT_POS = 23810
adct_count = 0

for b in blocks:
    if b.get('anchor_artigo') == 233:
        b['anchor_artigo'] = None
        b['anchor_slug'] = 'adct'
        b['anchor_paragrafo'] = None
        b['anchor_inciso'] = None
        b['anchor_alinea'] = None
        adct_count += 1
    elif b.get('paragraph_start') and b['paragraph_start'] >= ADCT_POS and b.get('anchor_artigo') is not None:
        # Check if this article anchor was placed after ADCT
        # Only reclassify if it looks like ADCT content
        pass

print(f"CORRECAO 1: Art. 233 -> ADCT: {adct_count} blocos reclassificados")

# ══════════════════════════════════════════
# CORREÇÃO 2 — Extrai relator, classe, numero, ano
# ══════════════════════════════════════════

def extrai_relator(metadata_text):
    if not metadata_text:
        return None
    m = re.search(r'rel\.\s+(?:min\.\s+)?([A-Z\u00c0-\u00dc][^,\.\]]+?)(?:\s*,|\s*\.|\s*\])', metadata_text, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r'red\.\s+do\s+ac\.\s+min\.\s+([^,\.\]]+?)(?:\s*,|\s*\.|\s*\])', metadata_text, re.I)
    if m:
        return m.group(1).strip()
    return None

CLASSES = r'ADI|ADC|ADPF|ADO|RE|ARE|HC|RHC|MS|MI|AP|ACO|Rcl|AI|Pet|SS|SL|IF|Inq|Ext|AC|AgR|ED|MC|QO|SV|PSV|AO|AR|RMS|CR|Rp|STA'

def extrai_meta(metadata_text):
    meta = {'relator': None, 'classe': None, 'numero': None, 'ano': None}
    if not metadata_text:
        return meta
    # Classe e numero
    m = re.match(rf'\[?\s*({CLASSES})\s*[\.\-\s]*([\d][\d\.,]*)', metadata_text, re.I)
    if m:
        meta['classe'] = m.group(1).upper()
        meta['numero'] = m.group(2).replace('.', '').replace(',', '')
    # Ano do julgamento
    m = re.search(r'j\.\s+\d{1,2}[-\./]\d{1,2}[-\./](\d{4})', metadata_text)
    if m:
        meta['ano'] = int(m.group(1))
    else:
        # Tenta outro formato: j. 1-7-2010
        m = re.search(r'j\.\s+\d{1,2}-\d{1,2}-(\d{4})', metadata_text)
        if m:
            meta['ano'] = int(m.group(1))
    # Relator
    meta['relator'] = extrai_relator(metadata_text)
    return meta

updated = 0
for b in blocks:
    meta_text = b.get('metadata_text', '')
    if meta_text:
        meta = extrai_meta(meta_text)
        # Só atualiza se extraiu algo novo
        if meta['relator']:
            b['relator'] = meta['relator']
        if meta['classe']:
            b['process_class'] = meta['classe']
        if meta['numero']:
            b['process_number'] = meta['numero']
        if meta['ano']:
            b['ano'] = meta['ano']
        updated += 1
    # Garante campos existem
    if 'ano' not in b:
        b['ano'] = None

print(f"CORRECAO 2: Metadados atualizados em {updated} blocos")

# ══════════════════════════════════════════
# SALVAR
# ══════════════════════════════════════════

import csv

with open(os.path.join(OUT, 'commentary_blocks.json'), 'w', encoding='utf-8') as f:
    json.dump(blocks, f, ensure_ascii=False, indent=2)

with open(os.path.join(OUT, 'commentary_blocks.tsv'), 'w', encoding='utf-8-sig', newline='') as f:
    if blocks:
        fieldnames = list(blocks[0].keys())
        # Ensure all blocks have all fields
        all_keys = set()
        for b in blocks:
            all_keys.update(b.keys())
        fieldnames = sorted(all_keys)
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore')
        w.writeheader()
        for b in blocks:
            row = {k: b.get(k, '') for k in fieldnames}
            w.writerow(row)

print(f"\nArquivos salvos.")

# ══════════════════════════════════════════
# DIAGNOSTICO FINAL
# ══════════════════════════════════════════

arts_cobertos = set(b['anchor_artigo'] for b in blocks if b['anchor_artigo'])
faltando = sorted(set(range(1, 251)) - arts_cobertos)
por_artigo = Counter(b['anchor_artigo'] for b in blocks if b['anchor_artigo'])
por_editorial = Counter(b['editorial_marker'] for b in blocks)

adct_blocks = [b for b in blocks if b.get('anchor_slug') == 'adct']
art233 = [b for b in blocks if b.get('anchor_artigo') == 233]

relatores = Counter(b.get('relator') for b in blocks if b.get('relator'))
classes = Counter(b.get('process_class') for b in blocks if b.get('process_class'))
anos = Counter(b.get('ano') for b in blocks if b.get('ano'))

print(f"\n{'='*70}")
print(f"  DIAGNOSTICO FINAL — PARSER v8 CORRIGIDO")
print(f"{'='*70}")

print(f"\n  RESUMO")
print(f"  Blocos resolvidos:         {len(blocks)}")
print(f"  Artigos cobertos:          {len(arts_cobertos)} de 250")
print(f"  Artigos sem decisao:       {len(faltando)}")
print(f"  Art. 233:                  {len(art233)} blocos (esperado: 0)")
print(f"  Blocos ADCT:               {len(adct_blocks)}")
print(f"  Blocos com processo:       {sum(1 for b in blocks if b.get('process_class'))}")
print(f"  Blocos com relator:        {sum(1 for b in blocks if b.get('relator'))}")
print(f"  Blocos com ano:            {sum(1 for b in blocks if b.get('ano'))}")
print(f"  Relatores distintos:       {len(relatores)}")
print(f"  Classes distintas:         {len(classes)}")

print(f"\n  ARTIGOS FALTANDO ({len(faltando)}):")
print(f"  {faltando}")

print(f"\n  TOP 10 ARTIGOS:")
for art, n in por_artigo.most_common(10):
    print(f"    Art. {art:3d}: {n:5d} blocos")

print(f"\n  TOP 15 RELATORES:")
for r, n in relatores.most_common(15):
    print(f"    {r:35s} {n:5d}")

print(f"\n  TOP 15 CLASSES:")
for c, n in classes.most_common(15):
    print(f"    {c:10s} {n:5d}")

print(f"\n  POR EDITORIAL:")
for ed, n in por_editorial.most_common():
    print(f"    {ed:30s} {n:5d}")

print(f"\n  TOP 10 ANOS:")
for ano, n in sorted(anos.items(), key=lambda x: -x[1])[:10]:
    print(f"    {ano}: {n}")

print(f"\n  Tamanhos:")
for fname in ["commentary_blocks.json", "commentary_blocks.tsv"]:
    fpath = os.path.join(OUT, fname)
    print(f"    {fname}: {os.path.getsize(fpath)/1024:.0f} KB")

print(f"\n{'='*70}")
print(f"  FIM")
print(f"{'='*70}")
