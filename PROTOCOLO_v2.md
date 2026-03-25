# PROTOCOLO ONTOLÓGICO UNIVERSAL v2

## Cartografia do Litigioso Brasileiro

---

# 1. ÂNCORA E FINALIDADE

**Autora:** Damares Medina
**Objeto:** Cartografia do litigioso brasileiro
**Princípio:** O sistema modela **relações entre estruturas normativas, documentos jurídicos e atores institucionais**, em múltiplos domínios e escalas.

---

# 2. PRINCÍPIOS INEGOCIÁVEIS

1. Todo corpus jurídico é uma **árvore multinível**
2. O artigo **não é a raiz** da estrutura normativa
3. Todo objeto possui **identidade estável (slug)**
4. Estrutura ≠ texto ≠ derivação
5. Embeddings são **derivados, nunca estruturais**
6. A base é **corpus-agnóstica e hierarquia-aware**
7. Nenhuma camada depende do frontend
8. **Domínios são dados, não estrutura** — crescem por INSERT, nunca por ALTER TABLE
9. **Cross-edges são consequência** — qualquer edge entre domínios diferentes é automaticamente um cross-edge
10. **Toda informação tem origem rastreável** — provenance é obrigatório

---

# 3. ARQUITETURA EM CAMADAS

```text
CAMADA 0 — DOMÍNIOS
  domains (hierárquicos, expansíveis)

CAMADA 1 — TAXONOMIAS VIVAS
  object_types · actor_types · event_types · edge_types
  role_types · subject_types
  (cada uma com domain_slug)

CAMADA 2 — PRIMITIVOS UNIVERSAIS (schema fixo, nunca muda)
  objects · actors · events · edges

CAMADA 3 — PROVENANCE (rastreabilidade horizontal)
  provenance (cruza todas as tabelas)

CAMADA 4 — DERIVADOS (reconstruíveis)
  chunks · embeddings · published_objects

CAMADA 5 — PADRÕES (views e métricas)
  materialized_patterns · views analíticas
```

---

# 4. CAMADA 0 — DOMÍNIOS

## 4.1 Definição

Um domínio é um **sistema institucional autônomo** com seus próprios objetos, atores, eventos e arestas. Domínios são dados — entram por INSERT, nunca por redesenho.

## 4.2 Estrutura

```
domains
  domain_slug           text PK
  label                 text NOT NULL
  parent_domain_slug    text FK → domains (nullable)
  valid_from            timestamptz
```

## 4.3 Hierarquia de domínios

```text
normativo
juridico
  └── stf
  └── stj
  └── tst
executivo
  └── presidencia
  └── agu
  └── pgfn
mp
  └── pgr
  └── mpf
legislativo
  └── senado
  └── camara
controle
  └── tcu
  └── cnj
```

O `parent_domain_slug` é opcional. Permite zoom: "todas as edges do domínio jurídico" inclui stf + stj + tst.

## 4.4 Ground zero

Hoje existem 2 domínios: `normativo` e `juridico`. Amanhã: INSERT.

## 4.5 Regra

> Nunca hardcodar a quantidade de domínios. O schema deve funcionar com 2 ou com 200.

---

# 5. CAMADA 1 — TAXONOMIAS VIVAS

Taxonomias são dados, nunca enums. Crescem por INSERT.

Cada taxonomia pertence a um domínio via `domain_slug`.

## 5.1 `object_types`

```
object_types
  type_slug             text PK
  domain_slug           text FK → domains
  label                 text
  valid_from            timestamptz
```

Exemplos:

| type_slug | domain_slug | label |
|---|---|---|
| constituicao | normativo | Constituição |
| emenda_constitucional | normativo | Emenda Constitucional |
| acao_direta | juridico | Ação Direta |
| recurso_extraordinario | juridico | Recurso Extraordinário |
| decreto | executivo | Decreto |
| projeto_lei | legislativo | Projeto de Lei |

## 5.2 `actor_types`

```
actor_types
  type_slug             text PK
  domain_slug           text FK → domains
  label                 text
  valid_from            timestamptz
```

## 5.3 `event_types`

```
event_types
  type_slug             text PK
  domain_slug           text FK → domains
  label                 text
  valid_from            timestamptz
```

## 5.4 `edge_types`

```
edge_types
  type_slug             text PK
  source_domain_slug    text FK → domains
  target_domain_slug    text FK → domains
  label                 text
  bidirectional         boolean DEFAULT false
  valid_from            timestamptz
```

### Regra dos edge_types

> Quando `source_domain_slug = target_domain_slug`, a aresta é **interna** ao domínio.
> Quando são diferentes, a aresta é um **cross-edge** — a zona de integração.
> A zona de integração não é uma camada. É uma propriedade emergente.

Exemplos:

| type_slug | source | target | label |
|---|---|---|---|
| interpreta | juridico | normativo | interpreta dispositivo |
| aplica | juridico | normativo | aplica norma |
| questiona | juridico | normativo | questiona constitucionalidade |
| nomeia_ministro | executivo | juridico | nomeia ministro |
| veta | executivo | legislativo | veta projeto |
| denuncia | mp | juridico | oferece denúncia |
| emenda | legislativo | normativo | emenda constituição |
| parent_of | normativo | normativo | relação hierárquica (interna) |
| relator_de | juridico | juridico | relator do processo (interna) |

## 5.5 `role_types` e `subject_types`

```
role_types
  type_slug             text PK
  domain_slug           text FK → domains
  label                 text
  valid_from            timestamptz

subject_types
  type_slug             text PK
  label                 text
  valid_from            timestamptz
```

---

# 6. CAMADA 2 — PRIMITIVOS UNIVERSAIS

Schema fixo. Nunca muda. Tudo é instância de um destes quatro.

## 6.1 `objects`

```
objects
  slug                  text PK
  type_slug             text FK → object_types
  payload               jsonb
  hash_content          text
  valid_from            timestamptz
  recorded_at           timestamptz DEFAULT now()
```

> `norm_object` = object. `legal_object` = object. `decreto` = object.
> A diferença está no `type_slug`, que aponta para o domínio.

## 6.2 `actors`

```
actors
  slug                  text PK
  type_slug             text FK → actor_types
  payload               jsonb
  dedup_hash            text
  succession_slug       text FK → actors (nullable)
  recorded_at           timestamptz DEFAULT now()
```

## 6.3 `events`

Append-only. Imutável.

```
events
  event_id              uuid PK
  type_slug             text FK → event_types
  aggregate_slug        text
  actor_slug            text FK → actors (nullable)
  payload               jsonb
  causation_id          uuid FK → events (nullable)
  occurred_at           timestamptz
  recorded_at           timestamptz DEFAULT now()
```

> O estado de um object é derivado da sequência de events cujo `aggregate_slug = object.slug`, ordenados por `occurred_at`.

## 6.4 `edges`

Grafo tipado universal.

```
edges
  edge_id               uuid PK
  type_slug             text FK → edge_types
  source_slug           text
  target_slug           text
  weight                float (nullable)
  payload               jsonb (nullable)
  valid_from            timestamptz (nullable)
  valid_to              timestamptz (nullable)
  causation_event_id    uuid FK → events (nullable)
  recorded_at           timestamptz DEFAULT now()
```

## 6.5 Três tempos irredutíveis

| Tempo | Campo | Significado |
|---|---|---|
| real | `occurred_at` | quando aconteceu no mundo |
| vigência | `valid_from` / `valid_to` | quando estava/está em vigor |
| registro | `recorded_at` | quando o sistema soube |

> Presentes em todo primitivo.

## 6.6 Regra

> Toda entidade especializada é instância de um destes quatro.
> `constituicao` = object. `ministro` = actor. `julgamento` = event. `interpreta` = edge.

---

# 7. ÁRVORE UNIVERSAL

## 7.1 Definição

A árvore é modelada por **edges do tipo `parent_of`** entre objects. Não existe tabela separada de nós — o nó é um object com type que indica sua posição na hierarquia (artigo, inciso, parágrafo...).

## 7.2 Tipos de nó (via object_types, domain: normativo)

* livro, parte, título, capítulo, seção, subseção
* artigo, caput, parágrafo, inciso, alínea, item, anexo

## 7.3 Campos estruturais (no payload do object)

* `parent_slug` — slug do nó pai
* `path_slug` — caminho completo na árvore
* `depth_level` — profundidade
* `sibling_order` — ordem entre irmãos
* `is_leaf` — se é folha
* `is_repealed` — se foi revogado
* `text_content` — texto original
* `normalized_text` — texto normalizado

## 7.4 Regra

> Nenhum nó pode existir sem saber sua posição na árvore.

---

# 8. CONVENÇÃO DE SLUG

## 8.1 Princípios

* determinística
* estável
* legível
* independente de contexto

## 8.2 Formato

| Nível | Exemplo |
|---|---|
| obra | `cf-1988` |
| versão | `cf-1988-2026` |
| artigo | `cf-1988-art-5` |
| caput | `cf-1988-art-5-caput` |
| inciso | `cf-1988-art-5-inc-ix` |
| alínea | `cf-1988-art-5-inc-ix-ali-a` |
| parágrafo | `cf-1988-art-5-par-1` |

## 8.3 Caminho completo

```text
cf-1988/titulo-2/capitulo-1/art-5/inc-ix
```

## 8.4 Regra

> Slug identifica o objeto. Path identifica a posição.

---

# 9. CAMADA 3 — PROVENANCE

## 9.1 Definição

Todo dado tem origem. Provenance é obrigatório para rastreabilidade e automação.

## 9.2 Estrutura

```
provenance
  provenance_id         uuid PK
  target_slug           text NOT NULL
  target_table          text NOT NULL
  source_type           text NOT NULL
  source_url            text
  pipeline_version      text
  confidence            float
  hash_input            text
  hash_output           text
  produced_at           timestamptz DEFAULT now()
```

## 9.3 source_types possíveis

* `manual` — inserido por humano
* `scraping` — extraído de fonte web
* `parsing` — derivado de documento (PDF, DOCX, HTML)
* `pipeline` — produzido por transformação automática
* `ia` — inferido por modelo de linguagem

## 9.4 Regras

> Nenhum dado entra no sistema sem provenance.
> Quando o pipeline muda de versão, os dados podem ser reprocessados via hash_input.
> Confidence permite ordenar fontes conflitantes.

---

# 10. CAMADA 4 — DERIVADOS

Reconstruíveis a partir das camadas anteriores. Nunca são base primária.

## 10.1 `chunks`

```
chunks
  chunk_slug            text PK
  object_slug           text NOT NULL
  chunk_text            text NOT NULL
  chunk_index           integer NOT NULL
  token_estimate        integer
  hash_chunk            text
```

## 10.2 `embeddings`

```
embeddings
  chunk_slug            text FK → chunks
  embedding_model       text NOT NULL
  vector_ref            vector(1536)
  created_at            timestamptz DEFAULT now()
  UNIQUE (chunk_slug, embedding_model)
```

## 10.3 `published_objects`

```
published_objects
  slug                  text PK
  payload_json          jsonb NOT NULL
  payload_hash          text NOT NULL
  updated_at            timestamptz DEFAULT now()
```

## 10.4 Regra

> Embedding nunca substitui estrutura.
> JSON nunca é base primária.

---

# 11. IDENTIDADE MULTINÍVEL

| Nível | Campo | Função |
|---|---|---|
| identidade | slug | quem é |
| domínio | type_slug → domain_slug | a que sistema pertence |
| versão | hash_content | em que estado está |
| granularidade | chunk_slug | para busca semântica |
| posição | path_slug | onde está na árvore |
| origem | provenance_id | de onde veio |

---

# 12. REGRAS DE VÍNCULO

1. Vincular ao nó mais específico
2. Nunca colapsar no caput
3. Subir por agregação
4. Registrar incerteza (confidence no provenance)
5. Separar vínculo inferido de vínculo confirmado (source_type no provenance)

---

# 13. ESCALABILIDADE

## Chaves estruturais

* `domain_slug`
* `type_slug`
* `object.slug`
* `valid_from` / `valid_to`

## Estratégia

* rebuild parcial por domínio
* reindexação por hash
* chunking incremental
* embeddings sob demanda
* expansão por INSERT em domains + types

---

# 14. BUSCA

## 14.1 Lexical
* palavra exata
* filtros por domínio, type, período

## 14.2 Semântica
* similaridade via embeddings

## 14.3 Híbrida
* filtro + ranking semântico

---

# 15. PIPELINE

1. ingestão (RAW)
2. canonização (slug, type, domain)
3. parsing (extração estruturada)
4. vinculação (edges entre objects)
5. provenance (registro de origem)
6. normalização (texto limpo)
7. chunking (segmentação)
8. embeddings (representação semântica)
9. indexação (padrões e métricas)
10. publicação (published_objects)

---

# 16. ERROS PROIBIDOS

* colapsar estrutura
* modelar por tela
* usar slug como única estrutura
* misturar camadas
* embeddar antes de estruturar
* perder vínculo com fonte
* **hardcodar quantidade de domínios**
* **tratar zona de integração como camada fixa**
* **inserir dado sem provenance**

---

# 17. FÓRMULA DE EXPANSÃO

```text
1. INSERT em domains (novo sistema)
2. INSERT em *_types com domain_slug (vocabulário)
3. INSERT em objects · actors · events · edges (fatos)
4. INSERT em provenance (origem)
5. Derivados se recalculam automaticamente

Nunca ALTER TABLE. Nunca redesenho. Nunca partir do zero.
```

---

# 18. FÓRMULA FINAL

```text
DOMAINS (N, hierárquicos)
→ TAXONOMIAS (com domain_slug)
→ PRIMITIVOS (objects · actors · events · edges)
→ PROVENANCE (rastreabilidade)
→ DERIVADOS (chunks · embeddings · JSON)
→ PADRÕES (views · métricas)
→ API / VIEWS
```

---

# 19. PRINCÍPIO FINAL

> O sistema não organiza textos.
> Ele organiza relações estruturadas entre textos, decisões, normas e instituições, em múltiplos domínios e escalas.
> O átomo de hoje é a cartografia do contencioso constitucional.
> O cosmos de amanhã é INSERT.

---

**Este protocolo define a arquitetura permanente do sistema.
Nenhuma implementação deve violar suas regras estruturais.**

**v2 — 25 de março de 2026**
**Damares Medina**
