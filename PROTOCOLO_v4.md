# PROTOCOLO ONTOLÓGICO UNIVERSAL v4

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
11. **Existem apenas 4 primitivos** — tudo é object, actor, event ou edge. Sem exceções.
12. **Estado é derivado, não armazenado** — o estado atual de um object é o último event sobre ele
13. **Temas são objects** — subjects são vinculados por edges, não por campos
14. **Slugs são globalmente únicos** — nenhum slug pode existir em mais de uma tabela de primitivos
15. **Edge é fonte de verdade para relações** — campos estruturais no payload são cache derivado

---

# 3. ARQUITETURA EM CAMADAS

```text
CAMADA 0 — DOMÍNIOS
  domains (hierárquicos, expansíveis)

CAMADA 1 — TAXONOMIAS VIVAS
  object_types · actor_types · event_types · edge_types
  state_types
  (cada uma com domain_slug — nullable para entidades transversais)

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
transversal               ← entidades que cruzam todos os domínios
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

O domínio `transversal` abriga entidades que não pertencem a nenhum sistema específico (subjects, anotações editoriais, etc.).

## 4.4 Ground zero

Hoje existem 3 domínios: `transversal`, `normativo` e `juridico`. Amanhã: INSERT.

## 4.5 Regra

> Nunca hardcodar a quantidade de domínios. O schema deve funcionar com 2 ou com 200.

---

# 5. CAMADA 1 — TAXONOMIAS VIVAS

Taxonomias são dados, nunca enums. Crescem por INSERT.

Cada taxonomia pertence a um domínio via `domain_slug`. O domain_slug é **nullable** para entidades que cruzam domínios (ex: edge_types que conectam qualquer par de domínios).

## 5.1 `object_types`

```
object_types
  type_slug             text PK
  domain_slug           text FK → domains (nullable)
  label                 text
  valid_from            timestamptz
```

Exemplos:

| type_slug | domain_slug | label |
|---|---|---|
| constituicao | normativo | Constituição |
| versao_normativa | normativo | Versão de obra normativa |
| emenda_constitucional | normativo | Emenda Constitucional |
| artigo | normativo | Artigo |
| inciso | normativo | Inciso |
| paragrafo | normativo | Parágrafo |
| alinea | normativo | Alínea |
| caput | normativo | Caput |
| titulo | normativo | Título |
| capitulo | normativo | Capítulo |
| secao | normativo | Seção |
| acao_direta | juridico | Ação Direta |
| recurso_extraordinario | juridico | Recurso Extraordinário |
| sumula_vinculante | juridico | Súmula Vinculante |
| decreto | executivo | Decreto |
| projeto_lei | legislativo | Projeto de Lei |
| subject | transversal | Tema/assunto |
| anotacao | transversal | Anotação editorial |

## 5.2 `actor_types`

```
actor_types
  type_slug             text PK
  domain_slug           text FK → domains (nullable)
  label                 text
  valid_from            timestamptz
```

Exemplos:

| type_slug | domain_slug | label |
|---|---|---|
| ministro_stf | juridico | Ministro do STF |
| presidente | executivo | Presidente da República |
| procurador_geral | mp | Procurador-Geral da República |
| senador | legislativo | Senador |
| deputado | legislativo | Deputado Federal |

## 5.3 `event_types`

```
event_types
  type_slug             text PK
  domain_slug           text FK → domains (nullable)
  label                 text
  valid_from            timestamptz
```

Exemplos:

| type_slug | domain_slug | label |
|---|---|---|
| julgamento | juridico | Julgamento |
| distribuicao | juridico | Distribuição |
| publicacao_dje | juridico | Publicação no DJe |
| promulgacao | normativo | Promulgação |
| nomeacao | executivo | Nomeação |
| mudanca_estado | transversal | Transição de estado |

## 5.4 `edge_types`

```
edge_types
  type_slug             text PK
  source_domain_slug    text FK → domains (nullable)
  target_domain_slug    text FK → domains (nullable)
  label                 text
  bidirectional         boolean DEFAULT false
  valid_from            timestamptz
```

### Regra dos edge_types

> Quando `source_domain_slug = target_domain_slug`, a aresta é **interna** ao domínio.
> Quando são diferentes, a aresta é um **cross-edge** — a zona de integração.
> Quando um ou ambos são NULL, a aresta é **transversal** — conecta qualquer domínio.
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
| parent_of | NULL | NULL | relação hierárquica (qualquer domínio) |
| version_of | normativo | normativo | versão de uma obra (interna) |
| relator_de | juridico | juridico | relator do processo (interna) |
| sobre | NULL | NULL | vincula object a subject/tema (transversal) |
| annota | NULL | NULL | vincula anotação a qualquer object (transversal) |
| exerce_papel | NULL | NULL | actor exerce papel em contexto (transversal) |

## 5.5 `state_types`

Define os estados possíveis para cada tipo de object em cada domínio.

```
state_types
  type_slug             text PK
  domain_slug           text FK → domains
  object_type_slug      text FK → object_types
  label                 text
  terminal              boolean DEFAULT false
  valid_from            timestamptz
```

Exemplos:

| type_slug | domain | object_type | label | terminal |
|---|---|---|---|---|
| distribuida | juridico | acao_direta | Distribuída | false |
| pautada | juridico | acao_direta | Pautada | false |
| julgada | juridico | acao_direta | Julgada | false |
| transitada | juridico | acao_direta | Transitada em julgado | true |
| vigente | normativo | artigo | Vigente | false |
| suspensa | normativo | artigo | Suspensa por liminar | false |
| revogada | normativo | artigo | Revogada | true |

### Regra de derivação de estado

> O estado atual de um object é determinado pelo **último event** cujo `aggregate_slug = object.slug` e cujo payload contenha `to_state`, ordenado por `occurred_at`.

> O campo `terminal` indica se o ciclo de vida do object chegou ao fim. Objects em estado terminal não recebem novos events de mudança de estado.

### Formato do event de transição de estado

```json
{
  "from_state": "distribuida",
  "to_state": "pautada",
  "reason": "inclusão em pauta pelo relator"
}
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
  valid_to              timestamptz (nullable)
  recorded_at           timestamptz DEFAULT now()
```

## 6.2 `actors`

```
actors
  slug                  text PK
  type_slug             text FK → actor_types
  payload               jsonb
  dedup_hash            text
  succession_slug       text FK → actors (nullable)
  valid_from            timestamptz
  valid_to              timestamptz (nullable)
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
  source_slug           text NOT NULL
  target_slug           text NOT NULL
  weight                float (nullable)
  payload               jsonb (nullable)
  valid_from            timestamptz (nullable)
  valid_to              timestamptz (nullable)
  causation_event_id    uuid FK → events (nullable)
  recorded_at           timestamptz DEFAULT now()
```

## 6.5 Unicidade global de slugs

> Slugs são **globalmente únicos** entre objects e actors. Nenhum slug pode existir simultaneamente nas duas tabelas.

> A convenção de slug garante isso por construção:
> - Objects de norma: `cf-1988`, `cf-1988-art-5`
> - Objects de decisão: `stf-adi-4650`
> - Objects de subject: `subject-saude`
> - Actors: `ministro-barroso`, `presidente-lula`

> Se um edge aponta para `source_slug = "ministro-barroso"`, o sistema sabe sem ambiguidade que é um actor, porque esse slug só existe em uma tabela.

## 6.6 Três tempos irredutíveis

Cada primitivo possui os tempos que fazem sentido para sua natureza:

| Primitivo | occurred_at | valid_from/to | recorded_at |
|---|---|---|---|
| objects | — | sim | sim |
| actors | — | sim | sim |
| events | sim | — | sim |
| edges | — | sim | sim |

* **occurred_at** — quando aconteceu no mundo real (só events, porque events são o que acontece)
* **valid_from / valid_to** — período de vigência (objects, actors, edges — coisas que existem no tempo)
* **recorded_at** — quando o sistema registrou (todos, sempre)

## 6.7 Regra

> Toda entidade especializada é instância de um destes quatro.
> `constituicao` = object. `ministro` = actor. `julgamento` = event. `interpreta` = edge. `anotacao` = object.

---

# 7. EQUIVALÊNCIA v1 → v4

As 9 entidades do protocolo v1 são instâncias dos 4 primitivos:

| v1 | v4 | Como |
|---|---|---|
| `works` | object | type: `constituicao`, `codigo_penal`, etc. |
| `work_versions` | object | type: `versao_normativa`, com edge `version_of` → work |
| `legal_nodes` | object | type: `artigo`, `inciso`, `paragrafo`, etc., com edge `parent_of` |
| `documents` | object | type: `acao_direta`, `recurso_extraordinario`, etc. |
| `annotations` | object | type: `anotacao`, com edge `annota` → node alvo |
| `citations` | edge | type: `interpreta`, `aplica`, `cita`, etc. |
| `node_relationships` | edge | type: `parent_of`, `amends`, `revokes`, etc. |
| `chunks` | chunk (derivado) | sem mudança |
| `embeddings` | embedding (derivado) | sem mudança |

> Não existem mais 9 entidades. Existem 4 primitivos + taxonomias. Tudo cabe.

---

# 8. ÁRVORE UNIVERSAL

## 8.1 Definição

A árvore é modelada por **edges do tipo `parent_of`** entre objects. Não existe tabela separada de nós — o nó é um object com type que indica sua posição na hierarquia (artigo, inciso, parágrafo...).

## 8.2 Tipos de nó (via object_types, domain: normativo)

* livro, parte, título, capítulo, seção, subseção
* artigo, caput, parágrafo, inciso, alínea, item, anexo

## 8.3 Fonte de verdade e cache

A relação hierárquica é definida pelo **edge `parent_of`**. Este é a fonte de verdade.

O payload do object pode conter campos estruturais derivados como **cache de leitura**:

* `path_slug` — caminho completo na árvore (derivado dos edges `parent_of`)
* `depth_level` — profundidade (derivado)
* `sibling_order` — ordem entre irmãos (fonte de verdade, pois não é derivável dos edges)
* `is_leaf` — se é folha (derivado)
* `is_repealed` — se foi revogado (derivado do último event de estado)
* `text_content` — texto original (fonte de verdade)
* `normalized_text` — texto normalizado (derivado)

### Regra de cache

> Se um campo do payload pode ser recalculado a partir dos edges e events, ele é **cache derivado**. Se o cache divergir do edge, o edge vence.

> Campos que são fonte de verdade no payload: `text_content`, `sibling_order`.

## 8.4 Regra

> Nenhum nó pode existir sem um edge `parent_of` que o posicione na árvore (exceto a raiz).

---

# 9. SUBJECTS (TEMAS)

## 9.1 Definição

Subjects são **objects** do type `subject` (domain: `transversal`). Representam temas, áreas ou assuntos. Vinculam-se a outros objects via edges do tipo `sobre`.

## 9.2 Estrutura

```
object: subject-saude             (type: subject, payload: {area: "direito_fundamental"})
object: subject-tributario        (type: subject, payload: {area: "direito_publico"})
object: subject-meio-ambiente     (type: subject, payload: {area: "direito_difuso"})
object: subject-saude-publica     (type: subject, payload: {area: "politica_publica"})
```

## 9.3 Hierarquia de subjects

Subjects podem ter sub-subjects via edge `parent_of`:

```
subject-saude --[parent_of]--> subject-saude-publica
subject-saude --[parent_of]--> subject-saude-suplementar
subject-tributario --[parent_of]--> subject-icms
```

## 9.4 Vinculação

Qualquer object pode ter múltiplos subjects via edge `sobre`:

```
stf-adi-4650 --[sobre]--> subject-financiamento-eleitoral
stf-adi-4650 --[sobre]--> subject-direitos-politicos
cf-1988-art-196 --[sobre]--> subject-saude
```

## 9.5 Regras

> Subject é object, não campo. Vincula-se por edge, não por atributo.
> Um object pode ter múltiplos subjects.
> Subjects formam árvore própria via `parent_of`.
> Filtragem por tema = buscar edges do tipo `sobre` que apontam para o subject.

---

# 10. ANOTAÇÕES

## 10.1 Definição

Anotações são **objects** do type `anotacao` (domain: `transversal`). Representam comentários editoriais, observações ou referências vinculadas a qualquer object do sistema.

## 10.2 Estrutura

```
object: anotacao-cf1988-art5-ec45   (type: anotacao, payload: {
  text: "Artigo alterado pela EC 45/2004",
  author: "Damares Medina",
  annotation_type: "alteracao"
})
```

## 10.3 Vinculação

Anotações se vinculam ao alvo via edge `annota`:

```
anotacao-cf1988-art5-ec45 --[annota]--> cf-1988-art-5
```

## 10.4 Regra

> Vincular ao nó mais específico possível.
> Uma anotação é um object, não um event. Pode ser corrigida (atualização de payload + novo hash).
> Se quiser registrar quando a anotação foi criada, crie um event do tipo `criacao` com `aggregate_slug = anotacao.slug`.

---

# 11. PAPÉIS (ROLES)

## 11.1 Definição

Um papel é uma **função exercida por um actor em um contexto**. Papéis são modelados como **edges** do tipo `exerce_papel` entre um actor e o object/contexto onde o papel é exercido.

## 11.2 Estrutura

```
edge: ministro-barroso --[exerce_papel]--> stf-adi-4650
  payload: { role: "relator" }

edge: ministro-fux --[exerce_papel]--> stf-adi-4650
  payload: { role: "presidente_sessao" }

edge: presidente-lula --[exerce_papel]--> ministro-barroso
  payload: { role: "nomeador" }
```

## 11.3 Regra

> Papel não é tabela. Papel é edge com tipo `exerce_papel` e a especificação do papel no payload.
> O vocabulário de papéis possíveis pode ser mantido em um object do type `vocabulario_papeis` se necessário para validação.

---

# 12. CONVENÇÃO DE SLUG

## 12.1 Princípios

* determinística
* estável
* legível
* independente de contexto
* **globalmente única entre objects e actors**

## 12.2 Formato

| Categoria | Prefixo | Exemplo |
|---|---|---|
| obra normativa | (jurisdição) | `cf-1988` |
| versão | (obra)-v- | `cf-1988-v-2026` |
| título | (obra)-tit- | `cf-1988-tit-2` |
| capítulo | (obra)-tit-N-cap- | `cf-1988-tit-2-cap-1` |
| artigo | (obra)-art- | `cf-1988-art-5` |
| caput | (obra)-art-N-caput | `cf-1988-art-5-caput` |
| inciso | (obra)-art-N-inc- | `cf-1988-art-5-inc-ix` |
| alínea | (obra)-...-ali- | `cf-1988-art-5-inc-ix-ali-a` |
| parágrafo | (obra)-art-N-par- | `cf-1988-art-5-par-1` |
| decisão | (tribunal)-(classe)-(número) | `stf-adi-4650` |
| súmula | (tribunal)-sv-(número) | `stf-sv-11` |
| subject | subject- | `subject-saude` |
| anotação | anotacao- | `anotacao-cf1988-art5-ec45` |
| actor | (papel)-(nome) | `ministro-barroso` |

## 12.3 Caminho completo (path)

```text
cf-1988/tit-2/cap-1/art-5/inc-ix
```

> Path é derivado dos edges `parent_of`. Armazenado como cache no payload.

## 12.4 Regras

> Slug identifica o objeto. Path identifica a posição.
> Slug é globalmente único. Dois objetos em tabelas diferentes nunca compartilham slug.
> Slug nunca muda depois de criado (identidade estável).

---

# 13. CAMADA 3 — PROVENANCE

## 13.1 Definição

Todo dado tem origem. Provenance é obrigatório para rastreabilidade e automação.

## 13.2 Estrutura

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

## 13.3 source_types possíveis

* `manual` — inserido por humano
* `scraping` — extraído de fonte web
* `parsing` — derivado de documento (PDF, DOCX, HTML)
* `pipeline` — produzido por transformação automática
* `ia` — inferido por modelo de linguagem

## 13.4 Regras

> Nenhum dado entra no sistema sem provenance.
> Quando o pipeline muda de versão, os dados podem ser reprocessados via hash_input.
> Confidence permite ordenar fontes conflitantes.

---

# 14. CAMADA 4 — DERIVADOS

Reconstruíveis a partir das camadas anteriores. Nunca são base primária.

## 14.1 `chunks`

```
chunks
  chunk_slug            text PK
  object_slug           text NOT NULL
  chunk_text            text NOT NULL
  chunk_index           integer NOT NULL
  token_estimate        integer
  hash_chunk            text
```

## 14.2 `embeddings`

```
embeddings
  chunk_slug            text FK → chunks
  embedding_model       text NOT NULL
  vector_ref            vector(1536)
  created_at            timestamptz DEFAULT now()
  UNIQUE (chunk_slug, embedding_model)
```

## 14.3 `published_objects`

```
published_objects
  slug                  text PK
  payload_json          jsonb NOT NULL
  payload_hash          text NOT NULL
  updated_at            timestamptz DEFAULT now()
```

## 14.4 Regra

> Embedding nunca substitui estrutura.
> JSON nunca é base primária.

---

# 15. IDENTIDADE MULTINÍVEL

| Nível | Campo | Função |
|---|---|---|
| identidade | slug (globalmente único) | quem é |
| domínio | type_slug → domain_slug | a que sistema pertence |
| versão | hash_content | em que estado está |
| estado | último event com to_state | situação atual no ciclo de vida |
| tema | edges tipo `sobre` | de que assunto trata |
| papel | edges tipo `exerce_papel` | que função exerce no contexto |
| granularidade | chunk_slug | para busca semântica |
| posição | path_slug (cache derivado) | onde está na árvore |
| origem | provenance_id | de onde veio |

---

# 16. REGRAS DE VÍNCULO

1. Vincular ao nó mais específico
2. Nunca colapsar no caput
3. Subir por agregação
4. Registrar incerteza (confidence no provenance)
5. Separar vínculo inferido de vínculo confirmado (source_type no provenance)

---

# 17. ESCALABILIDADE

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

# 18. BUSCA

## 18.1 Lexical
* palavra exata
* filtros por domínio, type, subject, período

## 18.2 Semântica
* similaridade via embeddings

## 18.3 Híbrida
* filtro + ranking semântico

---

# 19. PIPELINE

1. ingestão (RAW)
2. canonização (slug, type, domain)
3. parsing (extração estruturada)
4. vinculação (edges entre objects)
5. provenance (registro de origem)
6. normalização (texto limpo)
7. atribuição de subjects (edges tipo `sobre`)
8. atribuição de estado inicial (event com `to_state`)
9. chunking (segmentação)
10. embeddings (representação semântica)
11. indexação (padrões e métricas)
12. publicação (published_objects)

---

# 20. ERROS PROIBIDOS

* colapsar estrutura
* modelar por tela
* usar slug como única estrutura
* misturar camadas
* embeddar antes de estruturar
* perder vínculo com fonte
* **hardcodar quantidade de domínios**
* **tratar zona de integração como camada fixa**
* **inserir dado sem provenance**
* **criar tabela separada para entidade que cabe nos 4 primitivos**
* **armazenar estado como campo — estado é sempre derivado de events**
* **usar campo para tema — tema é object vinculado por edge**
* **reutilizar slug entre tabelas — slugs são globalmente únicos**
* **tratar payload como fonte de verdade para relações — edges vencem**

---

# 21. FÓRMULA DE EXPANSÃO

```text
1. INSERT em domains (novo sistema)
2. INSERT em *_types com domain_slug (vocabulário)
3. INSERT em state_types (estados possíveis)
4. INSERT em objects · actors · events · edges (fatos)
5. INSERT em provenance (origem)
6. Derivados se recalculam automaticamente

Nunca ALTER TABLE. Nunca redesenho. Nunca partir do zero.
```

---

# 22. FÓRMULA FINAL

```text
DOMAINS (N, hierárquicos, inclui transversal)
→ TAXONOMIAS (object_types · actor_types · event_types · edge_types · state_types)
→ PRIMITIVOS (objects · actors · events · edges)
→ PROVENANCE (rastreabilidade)
→ DERIVADOS (chunks · embeddings · JSON)
→ PADRÕES (views · métricas)
→ API / VIEWS
```

---

# 23. PRINCÍPIO FINAL

> O sistema não organiza textos.
> Ele organiza relações estruturadas entre textos, decisões, normas e instituições, em múltiplos domínios e escalas.
> O átomo de hoje é a cartografia do contencioso constitucional.
> O cosmos de amanhã é INSERT.

---

**Este protocolo define a arquitetura permanente do sistema.
Nenhuma implementação deve violar suas regras estruturais.**

**v4 — 25 de março de 2026**
**Damares Medina**
