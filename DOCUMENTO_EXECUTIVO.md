# ONTOLOGIA INTEGRADA — DOCUMENTO EXECUTIVO

## Cartografia do Litigioso Brasileiro

**Autora:** Damares Medina
**Versão:** v9 — 25 de março de 2026

---

## O que é

Uma arquitetura ontológica universal para modelar o sistema de justiça brasileiro como **rede de relações estruturadas** entre normas, decisões, atores, argumentos e instituições — em múltiplos domínios e escalas.

O átomo é a cartografia do contencioso constitucional (CF-1988 + STF). O cosmos é o sistema de justiça inteiro.

---

## O que resolve

| Problema | Solução |
|---|---|
| Dados jurídicos fragmentados e isolados | Grafo tipado universal com 4 primitivos |
| Estrutura normativa achatada (artigo como raiz) | Árvore multinível com hierarquia completa |
| Mistura entre fato e interpretação | Classes epistêmicas por tipo de relação |
| Sistemas fixos que não escalam | Domínios como dados — expansão por INSERT |
| Perda de histórico e rastreabilidade | Event-sourcing + provenance obrigatório |
| Predição impossível sem sinais estruturados | Camada prospectiva com sinais decisórios |
| Análise manual e repetitiva | Sistema autoensinável com membrana ontológica |

---

## Arquitetura

```
CAMADA 0 — DOMÍNIOS (N, hierárquicos)
CAMADA 1 — TAXONOMIAS VIVAS (com classes ontológicas/epistêmicas)
CAMADA 2 — 4 PRIMITIVOS (objects · actors · events · edges)
CAMADA 3 — PROVENANCE (rastreabilidade)
CAMADA 4 — DERIVADOS (chunks · embeddings · JSON)
CAMADA 5 — VIEWS + PERFIS + MEMBRANA
```

---

## Os 4 primitivos

Tudo no sistema é instância de um destes quatro. Sem exceções.

| Primitivo | O que modela | Exemplo |
|---|---|---|
| **object** | qualquer entidade com existência | CF-1988, Art. 5º, ADI-4650, súmula, argumento |
| **actor** | qualquer agente que age | Ministro Barroso, PGR, sistema-pipeline |
| **event** | qualquer acontecimento | julgamento, distribuição, emenda aplicada |
| **edge** | qualquer relação entre entidades | interpreta, parent_of, exerce_papel |

Cada primitivo tem identidade dual: **UUID** (consistência interna) + **slug** (legibilidade pública).

---

## Domínios

Sistemas institucionais autônomos. Crescem por INSERT, nunca por redesenho.

| Domínio | Ground zero | Expansão futura |
|---|---|---|
| transversal | subjects, anotações, sistema | — |
| normativo | CF-1988, artigos, emendas | leis, códigos, decretos |
| juridico | STF, decisões, súmulas | STJ, TST, TRFs |
| executivo | — | presidência, AGU, PGFN |
| mp | — | PGR, MPF |
| legislativo | — | Senado, Câmara |
| controle | — | TCU, CNJ |

---

## Classificações

Cada tipo tem sua classificação que responde "o que é" (não apenas "a que sistema pertence"):

| Taxonomia | Classificação | Valores |
|---|---|---|
| object_types | ontological_class | estrutural, processual, semantico, editorial, argumentativo, analitico, preditivo |
| actor_types | actor_class | institucional, automatizado |
| event_types | event_class | juridico, normativo, manutencao, fiscal |
| edge_types | epistemic_class | estrutural, normativa, interpretativa, classificatoria, editorial, institucional, argumentativa, fiscal, preditiva |

---

## Camadas especializadas

### Sinais decisórios (camada prospectiva)

Todo julgamento registra obrigatoriamente: outcome, decision_direction, uses_modulation, reasoning_style, fiscal_effect, decision_body, adjudication_environment.

### Impacto orçamentário

3 níveis progressivos: edge com payload → object analítico → fórmulas derivadas (EFR, ICF, IDT, IIFD, IDC).

### Argumentos

Razões de decidir, teses e fundamentos como objects com edges `suporta`, `contradiz`, `fundamenta_em`, `confirma`, `supera`.

### Vida processual e ecologia decisória

Processo como linha de vida. Ambiente de julgamento (virtual/presencial/híbrido) como variável estruturante. Ecologia: relator × órgão × tema × ambiente × demais atores.

### Sistema autoensinável

Perfis decisórios por relator e órgão. Membrana ontológica de 3 níveis (observação → proposta → incorporação). O banco aprende; a ontologia decide o que vira conhecimento.

---

## Números

| Métrica | Valor |
|---|---|
| Princípios inegociáveis | 28 |
| Seções do protocolo | 32 |
| Erros proibidos | 28 |
| Primitivos | 4 |
| Domínios (ground zero) | 3 |
| Classes ontológicas | 7 |
| Classes epistêmicas | 9 |
| Object types definidos | 26 |
| Edge types definidos | 31 |
| Views definidas | 23 |
| Fórmulas analíticas | 12 |
| Passos do pipeline | 17 |
| Versões do protocolo | 9 |

---

## Regra de ouro

> O sistema não organiza textos.
> Ele organiza relações estruturadas entre textos, decisões, normas, instituições, argumentos e sinais decisórios, em múltiplos domínios, escalas e classes epistêmicas.
> O átomo de hoje é a cartografia do contencioso constitucional.
> O cosmos de amanhã é INSERT.
> A cartografia não apenas mapeia o passado — ela projeta o futuro.
> O banco aprende; a ontologia decide o que pode virar conhecimento estrutural.

---

**Damares Medina · v9 · 2026**
