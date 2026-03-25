# PROTOCOLO ONTOLÓGICO UNIVERSAL v5

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
11. **Existem apenas 4 primitivos** — tudo é object, actor, event ou edge. Sem exceções
12. **Estado é derivado, não armazenado** — o estado atual é o último event com `to_state`
13. **Temas são objects** — subjects são vinculados por edges, não por campos
14. **Slugs são globalmente únicos** — nenhum slug pode existir em mais de uma tabela de primitivos
15. **Edge é fonte de verdade para relações** — campos estruturais no payload são cache derivado
16. **Nunca DELETE, apenas encerrar** — dados incorretos recebem `valid_to` e event de `anulacao`
17. **source [verbo] target** — em todo edge, o source pratica a ação sobre o target

---

# 3. ARQUITETURA EM CAMADAS

```text
CAMADA 0 — DOMÍNIOS
  domains (hierárquicos, expansíveis)

CAMADA 1 — TAXONOMIAS VIVAS
  object_types · actor_types · event_types · edge_types
  state_types
  (domain_slug nullable para entidades transversais)

CAMADA 2 — PRIMITIVOS UNIVERSAIS (schema fixo, nunca muda)
  objects · actors · events · edges

CAMADA 3 — PROVENANCE (rastreabilidade horizontal)
  provenance (cruza todas as tabelas)

CAMADA 4 — DERIVADOS (reconstruíveis)
  chunks · embeddings · published_objects

CAMADA 5 — PADRÕES (views materializadas e métricas)
  views com domain_slug denormalizado para performance
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

O domínio `transversal` abriga entidades que não pertencem a nenhum sistema específico (subjects, anotações, actors de sistema).

## 4.4 Ground zero

Hoje existem 3 domínios: `transversal`, `normativo` e `juridico`. Amanhã: INSERT.

## 4.5 Regra

> Nunca hardcodar a quantidade de domínios. O schema deve funcionar com 2 ou com 200.

---

# 5. CAMADA 1 — TAXONOMIAS VIVAS

Taxonomias são dados, nunca enums. Crescem por INSERT.

O `domain_slug` é **nullable** — entidades transversais (subjects, edges universais) não pertencem a um domínio específico ou pertencem ao domínio `transversal`.

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
| titulo | normativo | Título |
| capitulo | normativo | Capítulo |
| secao | normativo | Seção |
| artigo | normativo | Artigo |
| caput | normativo | Caput |
| inciso | normativo | Inciso |
| paragrafo | normativo | Parágrafo |
| alinea | normativo | Alínea |
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
| sistema | transversal | Ator automatizado (pipeline, IA) |

> O actor `sistema-pipeline` (type: `sistema`) é usado como actor de events automatizados. Events sempre devem ter actor_slug preenchido — usar o actor de sistema quando o originador não é humano.

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
| correcao | transversal | Correção de dado existente |
| anulacao | transversal | Anulação de dado incorreto |
| criacao | transversal | Registro de criação |

## 5.4 `edge_types`

```
edge_types
  type_slug             text PK
  source_domain_slug    text FK → domains (nullable)
  target_domain_slug    text FK → domains (nullable)
  label                 text
  bidirectional         boolean DEFAULT false
  allows_multiple       boolean DEFAULT true
  valid_from            timestamptz
```

### Campo `allows_multiple`

> Quando `allows_multiple = false`, só pode existir **um edge deste tipo** entre o mesmo par source+target. Enforced via constraint:
> `UNIQUE (type_slug, source_slug, target_slug) WHERE type_slug IN (tipos com allows_multiple = false)`

> `parent_of` → allows_multiple = false (um nó só tem um pai)
> `sobre` → allows_multiple = true (um object pode ser sobre vários subjects)
> `interpreta` → allows_multiple = true (uma decisão pode interpretar o mesmo artigo mais de uma vez em contextos diferentes)

### Regra de direção

> **source [verbo] target** — em todo edge, o source pratica a ação descrita pelo tipo sobre o target.
> `stf-adi-4650 --[interpreta]--> cf-1988-art-5` lê-se: "ADI 4650 interpreta Art. 5º"
> `cf-1988 --[parent_of]--> cf-1988-tit-1` lê-se: "CF-1988 é pai do Título 1"

### Regra dos domínios

> Quando `source_domain_slug = target_domain_slug`: aresta **interna**.
> Quando são diferentes: **cross-edge** (zona de integração).
> Quando NULL: aresta **transversal** (conecta qualquer domínio).
> A zona de integração não é uma camada. É uma propriedade emergente.

Exemplos:

| type_slug | source | target | allows_multiple | label |
|---|---|---|---|---|
| interpreta | juridico | normativo | true | interpreta dispositivo |
| aplica | juridico | normativo | true | aplica norma |
| questiona | juridico | normativo | true | questiona constitucionalidade |
| nomeia_ministro | executivo | juridico | false | nomeia ministro |
| veta | executivo | legislativo | false | veta projeto |
| denuncia | mp | juridico | true | oferece denúncia |
| emenda | legislativo | normativo | true | emenda constituição |
| parent_of | NULL | NULL | false | relação hierárquica |
| version_of | normativo | normativo | false | versão de uma obra |
| relator_de | juridico | juridico | false | relator do processo |
| sobre | NULL | NULL | true | vincula a subject/tema |
| annota | NULL | NULL | true | vincula anotação ao alvo |
| exerce_papel | NULL | NULL | true | actor exerce papel em contexto |
| sucede | NULL | NULL | false | actor sucede outro |

### Semântica do weight

> O campo `weight` em edges tem semântica definida pelo `edge_type`. Cada edge_type pode declarar no seu payload o que weight significa:

```
edge_type: interpreta → weight = confidence da extração (0.0 a 1.0)
edge_type: sobre → weight = relevância do tema (0.0 a 1.0)
edge_type: parent_of → weight = NULL (não se aplica)
```

## 5.5 `state_types`

Define os estados possíveis para cada tipo de object em cada domínio.

```
state_types
  type_slug             text
  object_type_slug      text FK → object_types
  domain_slug           text FK → domains
  label                 text
  terminal              boolean DEFAULT false
  valid_from            timestamptz
  PRIMARY KEY (type_slug, object_type_slug)
```

> PK composta `(type_slug, object_type_slug)` permite que o mesmo estado "vigente" exista para artigo, inciso, parágrafo, etc.

Exemplos:

| type_slug | object_type | domain | label | terminal |
|---|---|---|---|---|
| vigente | artigo | normativo | Vigente | false |
| vigente | inciso | normativo | Vigente | false |
| vigente | paragrafo | normativo | Vigente | false |
| suspensa | artigo | normativo | Suspensa por liminar | false |
| revogada | artigo | normativo | Revogada | true |
| distribuida | acao_direta | juridico | Distribuída | false |
| pautada | acao_direta | juridico | Pautada | false |
| julgada | acao_direta | juridico | Julgada | false |
| transitada | acao_direta | juridico | Transitada em julgado | true |

### Regra de derivação de estado

> O estado atual de um object ou actor é determinado pelo **último event** cujo `aggregate_slug` = slug do alvo e cujo payload contenha `to_state`, ordenado por `occurred_at`.

> `aggregate_slug` pode apontar para **objects ou actors**. Ambos possuem ciclo de vida via events.

> O campo `terminal` indica se o ciclo de vida chegou ao fim.

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

### Mutabilidade

> Objects são **mutáveis com rastreio**. O payload pode ser atualizado (ex: correção de texto normalizado).

> Toda mutação obrigatoriamente gera:
> 1. Um event do tipo `correcao` com `aggregate_slug = object.slug` e payload contendo o `hash_anterior`
> 2. Atualização do `hash_content` no object
> 3. Novo registro de provenance com o hash atualizado

> Assim o histórico de mutações é reconstruível via events.

### Encerramento (nunca DELETE)

> Para remover um dado incorreto: setar `valid_to = now()` e criar event do tipo `anulacao` com razão no payload. O object permanece no banco mas está encerrado.

## 6.2 `actors`

```
actors
  slug                  text PK
  type_slug             text FK → actor_types
  payload               jsonb
  dedup_hash            text
  valid_from            timestamptz
  valid_to              timestamptz (nullable)
  recorded_at           timestamptz DEFAULT now()
```

> Sucessão entre actors é modelada via edge `sucede` (ex: `ministro-dino --[sucede]--> ministro-marco-aurelio`). Não existe campo `succession_slug`.

> Actors também possuem ciclo de vida via events: events com `aggregate_slug = actor.slug` registram nomeação, posse, aposentadoria, etc.

### Actors de sistema

> O actor `sistema-pipeline` (type: `sistema`, domain: `transversal`) é o autor de events automatizados. Todo event deve ter `actor_slug` preenchido.

## 6.3 `events`

Append-only. Imutável. Nunca UPDATE, nunca DELETE.

```
events
  event_id              uuid PK
  type_slug             text FK → event_types
  aggregate_slug        text NOT NULL
  actor_slug            text FK → actors NOT NULL
  payload               jsonb
  causation_id          uuid FK → events (nullable)
  occurred_at           timestamptz NOT NULL
  recorded_at           timestamptz DEFAULT now()
```

> `aggregate_slug` pode apontar para **objects ou actors**. Identifica sobre quem/o quê o event fala.

> `actor_slug` é **NOT NULL**. Todo event tem um autor (humano ou `sistema-pipeline`).

> `causation_id` permite encadear events: "este julgamento causou esta mudança de estado".

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

> Constraint para edge_types com `allows_multiple = false`:
> Não pode existir mais de um edge ativo (sem valid_to) do mesmo type entre o mesmo par source+target.

### Encerramento de edges

> Para "remover" um edge: setar `valid_to = now()`. O edge permanece no banco como histórico.
> Para corrigir um edge errado: encerrar o antigo + criar novo.

## 6.5 Unicidade global de slugs

> Slugs são **globalmente únicos** entre objects e actors. Garantido pela convenção de slug:

| Primitivo | Padrão de slug | Exemplo |
|---|---|---|
| object normativo | (obra)-(tipo)-(id) | `cf-1988-art-5` |
| object jurídico | (tribunal)-(classe)-(número) | `stf-adi-4650` |
| object subject | subject-(tema) | `subject-saude` |
| object anotação | anotacao-(contexto) | `anotacao-cf1988-art5-ec45` |
| actor | (papel)-(nome) | `ministro-barroso` |
| actor sistema | sistema-(nome) | `sistema-pipeline` |

> Events usam `event_id` (uuid), não slug. Edges usam `edge_id` (uuid), não slug. Não há risco de colisão com slugs de objects/actors.

## 6.6 Três tempos irredutíveis

Cada primitivo possui os tempos que fazem sentido para sua natureza:

| Primitivo | occurred_at | valid_from/to | recorded_at |
|---|---|---|---|
| objects | — | sim | sim |
| actors | — | sim | sim |
| events | sim | — | sim |
| edges | — | sim | sim |

* **occurred_at** — quando aconteceu no mundo real (só events)
* **valid_from / valid_to** — período de vigência (objects, actors, edges)
* **recorded_at** — quando o sistema registrou (todos, sempre)

## 6.7 Regra

> Toda entidade especializada é instância de um destes quatro.
> `constituicao` = object. `ministro` = actor. `julgamento` = event. `interpreta` = edge. `anotacao` = object.

---

# 7. EQUIVALÊNCIA v1 → v5

As 9 entidades do protocolo v1 são instâncias dos 4 primitivos:

| v1 | v5 | Como |
|---|---|---|
| `works` | object | type: `constituicao`, `codigo_penal`, etc. |
| `work_versions` | object | type: `versao_normativa`, com edge `version_of` → work |
| `legal_nodes` | object | type: `artigo`, `inciso`, etc., com edge `parent_of` |
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

A árvore é modelada por **edges do tipo `parent_of`** entre objects. Não existe tabela separada de nós — o nó é um object com type que indica sua posição na hierarquia.

## 8.2 Tipos de nó (via object_types, domain: normativo)

* livro, parte, título, capítulo, seção, subseção
* artigo, caput, parágrafo, inciso, alínea, item, anexo

## 8.3 Fonte de verdade e cache

| Campo no payload | Natureza | Regra |
|---|---|---|
| `text_content` | fonte de verdade | conteúdo original do dispositivo |
| `sibling_order` | fonte de verdade | ordem entre irmãos (não derivável dos edges) |
| `path_slug` | cache derivado | recalculável a partir dos edges `parent_of` |
| `depth_level` | cache derivado | recalculável |
| `is_leaf` | cache derivado | recalculável |
| `is_repealed` | cache derivado | derivado do último event de estado |
| `normalized_text` | cache derivado | derivado de `text_content` |

> Se o cache divergir do edge ou event, o edge/event vence. Cache pode ser reconstruído a qualquer momento.

## 8.4 Regras

> Nenhum nó pode existir sem um edge `parent_of` que o posicione na árvore (exceto a raiz).
> Edges `parent_of` só conectam objects do mesmo domínio ou sub-grafo hierárquico.
> Queries sobre árvore devem filtrar por domain_slug do object para evitar cruzamento com outras hierarquias (ex: subjects).

---

# 9. SUBJECTS (TEMAS)

## 9.1 Definição

Subjects são **objects** do type `subject` (domain: `transversal`). Representam temas, áreas ou assuntos.

## 9.2 Hierarquia

Subjects formam árvore própria via edge `parent_of`:

```
subject-saude --[parent_of]--> subject-saude-publica
subject-tributario --[parent_of]--> subject-icms
```

## 9.3 Vinculação

Qualquer object pode ter múltiplos subjects via edge `sobre`:

```
stf-adi-4650 --[sobre]--> subject-financiamento-eleitoral
cf-1988-art-196 --[sobre]--> subject-saude
```

## 9.4 Regras

> Subject é object, não campo.
> Vincula-se por edge `sobre`, não por atributo no payload.
> Um object pode ter múltiplos subjects.
> Filtragem por tema = buscar edges do tipo `sobre`.

---

# 10. ANOTAÇÕES

## 10.1 Definição

Anotações são **objects** do type `anotacao` (domain: `transversal`). Comentários editoriais vinculados a qualquer object.

## 10.2 Vinculação

```
anotacao-cf1988-art5-ec45 --[annota]--> cf-1988-art-5
```

## 10.3 Regras

> Anotação é object, não event. Pode ser corrigida (mutação com rastreio).
> Vincular ao nó mais específico possível.
> Para registrar quando foi criada: event do tipo `criacao` com `aggregate_slug = anotacao.slug`.

---

# 11. PAPÉIS (ROLES)

## 11.1 Definição

Papel = edge `exerce_papel` entre actor e object/contexto, com especificação no payload.

## 11.2 Estrutura

```
ministro-barroso --[exerce_papel]--> stf-adi-4650
  payload: { role: "relator" }

ministro-fux --[exerce_papel]--> stf-adi-4650
  payload: { role: "presidente_sessao" }
```

## 11.3 Regra

> Papel não é tabela nem taxonomia. É edge com tipo `exerce_papel` e especificação no payload.

---

# 12. CONVENÇÃO DE SLUG

## 12.1 Princípios

* determinística
* estável (nunca muda depois de criado)
* legível
* independente de contexto
* **globalmente única entre objects e actors**

## 12.2 Formato

| Categoria | Padrão | Exemplo |
|---|---|---|
| obra normativa | (jurisdição) | `cf-1988` |
| versão | (obra)-v-(ano) | `cf-1988-v-2026` |
| título | (obra)-tit-(n) | `cf-1988-tit-2` |
| capítulo | (obra)-tit-N-cap-(n) | `cf-1988-tit-2-cap-1` |
| artigo | (obra)-art-(n) | `cf-1988-art-5` |
| caput | (obra)-art-N-caput | `cf-1988-art-5-caput` |
| inciso | (obra)-art-N-inc-(rom) | `cf-1988-art-5-inc-ix` |
| alínea | ...-ali-(letra) | `cf-1988-art-5-inc-ix-ali-a` |
| parágrafo | (obra)-art-N-par-(n) | `cf-1988-art-5-par-1` |
| decisão | (tribunal)-(classe)-(número) | `stf-adi-4650` |
| súmula | (tribunal)-sv-(número) | `stf-sv-11` |
| subject | subject-(tema) | `subject-saude` |
| anotação | anotacao-(contexto) | `anotacao-cf1988-art5-ec45` |
| actor | (papel)-(nome) | `ministro-barroso` |
| actor sistema | sistema-(nome) | `sistema-pipeline` |

## 12.3 Caminho completo (path)

```text
cf-1988/tit-2/cap-1/art-5/inc-ix
```

> Path é cache derivado dos edges `parent_of`. Armazenado no payload para leitura rápida.

## 12.4 Regras

> Slug identifica o objeto. Path identifica a posição.
> Slug nunca muda. Dois primitivos nunca compartilham slug.

---

# 13. CAMADA 3 — PROVENANCE

## 13.1 Definição

Todo dado tem origem. Provenance é obrigatório.

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

> `target_slug` para objects e actors = slug. Para events = event_id (uuid como text). Para edges = edge_id (uuid como text).
> `target_table` desambigua: `objects`, `actors`, `events`, `edges`.

## 13.3 source_types

* `manual` — inserido por humano
* `scraping` — extraído de fonte web
* `parsing` — derivado de documento
* `pipeline` — transformação automática
* `ia` — inferido por modelo de linguagem

## 13.4 Regras

> Nenhum dado entra no sistema sem provenance.
> Quando o pipeline muda de versão, reprocessar via hash_input.
> Confidence permite ordenar fontes conflitantes.

---

# 14. CAMADA 4 — DERIVADOS

Reconstruíveis. Nunca são base primária.

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

# 15. CAMADA 5 — PADRÕES E VIEWS

## 15.1 Definição

Views materializadas para queries frequentes. Incluem `domain_slug` denormalizado para evitar joins de 2 hops.

## 15.2 Views essenciais (ground zero)

```
v_objects_with_domain
  slug, type_slug, domain_slug, payload, valid_from, valid_to

v_current_state
  slug, type_slug, domain_slug, current_state, last_event_at

v_tree_nodes
  slug, type_slug, parent_slug, path_slug, depth_level, sibling_order, domain_slug
```

> Views são recalculáveis. Não são fonte de verdade.

---

# 16. IDENTIDADE MULTINÍVEL

| Nível | Campo | Função |
|---|---|---|
| identidade | slug (globalmente único) | quem é |
| domínio | type_slug → domain_slug | a que sistema pertence |
| versão | hash_content | em que estado está |
| estado | último event com to_state | situação atual no ciclo de vida |
| tema | edges tipo `sobre` | de que assunto trata |
| papel | edges tipo `exerce_papel` | que função exerce no contexto |
| granularidade | chunk_slug | para busca semântica |
| posição | path_slug (cache) | onde está na árvore |
| origem | provenance_id | de onde veio |

---

# 17. REGRAS DE VÍNCULO

1. Vincular ao nó mais específico
2. Nunca colapsar no caput
3. Subir por agregação
4. Registrar incerteza (confidence no provenance)
5. Separar vínculo inferido de vínculo confirmado (source_type no provenance)

---

# 18. OPERAÇÕES SOBRE DADOS

## 18.1 Criar

INSERT em primitivo + INSERT em provenance. Sempre juntos.

## 18.2 Corrigir

UPDATE no payload do object/actor + event `correcao` com hash_anterior + novo provenance.

## 18.3 Encerrar

SET `valid_to = now()` no object/actor/edge + event `anulacao` com razão.

## 18.4 Nunca

> Nunca DELETE. Nunca UPDATE sem event de rastreio. Nunca INSERT sem provenance.

---

# 19. ESCALABILIDADE

## Chaves estruturais

* `domain_slug` (via type)
* `type_slug`
* `slug`
* `valid_from` / `valid_to`

## Índices recomendados

```
objects: (type_slug), (valid_from)
actors: (type_slug), (valid_from)
events: (aggregate_slug, occurred_at), (type_slug)
edges: (type_slug, source_slug), (type_slug, target_slug), (source_slug), (target_slug)
provenance: (target_slug, target_table)
```

## Estratégia

* rebuild parcial por domínio
* reindexação por hash
* chunking incremental
* embeddings sob demanda
* expansão por INSERT em domains + types

---

# 20. BUSCA

## 20.1 Lexical
* palavra exata
* filtros por domínio, type, subject, período

## 20.2 Semântica
* similaridade via embeddings

## 20.3 Híbrida
* filtro + ranking semântico

---

# 21. PIPELINE

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
11. materialização de views (padrões e métricas)
12. publicação (published_objects)

---

# 22. ERROS PROIBIDOS

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
* **usar DELETE para remover dados — encerrar com valid_to + event**
* **criar event sem actor — usar sistema-pipeline para events automatizados**
* **modelar relação como campo no primitivo — relação é edge**

---

# 23. FÓRMULA DE EXPANSÃO

```text
1. INSERT em domains (novo sistema)
2. INSERT em *_types com domain_slug (vocabulário)
3. INSERT em state_types (estados possíveis)
4. INSERT em objects · actors · events · edges (fatos)
5. INSERT em provenance (origem)
6. Materializar views
7. Derivados se recalculam automaticamente

Nunca ALTER TABLE. Nunca redesenho. Nunca partir do zero.
```

---

# 24. FÓRMULA FINAL

```text
DOMAINS (N, hierárquicos, inclui transversal)
→ TAXONOMIAS (object_types · actor_types · event_types · edge_types · state_types)
→ PRIMITIVOS (objects · actors · events · edges)
→ PROVENANCE (rastreabilidade)
→ VIEWS MATERIALIZADAS (domain denormalizado, estado atual, árvore)
→ DERIVADOS (chunks · embeddings · JSON)
→ API / VIEWS
```

---

# 25. PRINCÍPIO FINAL

> O sistema não organiza textos.
> Ele organiza relações estruturadas entre textos, decisões, normas e instituições, em múltiplos domínios e escalas.
> O átomo de hoje é a cartografia do contencioso constitucional.
> O cosmos de amanhã é INSERT.

---

**Este protocolo define a arquitetura permanente do sistema.
Nenhuma implementação deve violar suas regras estruturais.**

**v5 — 25 de março de 2026**
**Damares Medina**
