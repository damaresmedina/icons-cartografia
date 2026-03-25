# PROTOCOLO ONTOLÓGICO UNIVERSAL v6

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
18. **Versionamento é event-sourced** — nós são modificados in-place, histórico via events, versão é marco temporal
19. **Payload é convenção, não schema** — estrutura definida por type_slug, validação é do pipeline

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

O `domain_slug` é **nullable** — entidades transversais não pertencem a um domínio específico ou pertencem ao domínio `transversal`.

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
| versao_normativa | normativo | Versão/marco temporal de obra normativa |
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

> O actor `sistema-pipeline` (type: `sistema`) é o autor de events automatizados. Events sempre devem ter actor_slug preenchido.

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
| emenda_aplicada | normativo | Aplicação de emenda constitucional |
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

> Quando `allows_multiple = false`, só pode existir **um edge ativo** (sem valid_to) deste tipo entre o mesmo par source+target.

### Regra de direção

> **source [verbo] target** — o source pratica a ação sobre o target. Sempre.

### Regra dos domínios

> `source_domain = target_domain` → aresta **interna**.
> source ≠ target → **cross-edge** (zona de integração).
> NULL → aresta **transversal** (qualquer domínio).

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
| amends | normativo | normativo | true | emenda altera dispositivo |

### Semântica do weight

> O campo `weight` tem semântica definida pelo edge_type:
> `interpreta` → confidence da extração (0.0 a 1.0)
> `sobre` → relevância do tema (0.0 a 1.0)
> `parent_of` → NULL (não se aplica)

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

> PK composta permite que o mesmo estado "vigente" exista para artigo, inciso, parágrafo, etc.

Exemplos:

| type_slug | object_type | domain | label | terminal |
|---|---|---|---|---|
| vigente | artigo | normativo | Vigente | false |
| vigente | inciso | normativo | Vigente | false |
| vigente | paragrafo | normativo | Vigente | false |
| vigente | alinea | normativo | Vigente | false |
| suspensa | artigo | normativo | Suspensa por liminar | false |
| revogada | artigo | normativo | Revogada | true |
| distribuida | acao_direta | juridico | Distribuída | false |
| pautada | acao_direta | juridico | Pautada | false |
| julgada | acao_direta | juridico | Julgada | false |
| transitada | acao_direta | juridico | Transitada em julgado | true |

### Regra de derivação de estado

> O estado atual de um object ou actor é determinado pelo **último event** cujo `aggregate_slug` = slug do alvo e cujo payload contenha `to_state`, ordenado por `occurred_at`.

> `aggregate_slug` pode apontar para **objects ou actors**.

### Formato do event de transição

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

> Objects são **mutáveis com rastreio**. Toda mutação gera:
> 1. Event `correcao` com `aggregate_slug = object.slug` e `hash_anterior` no payload
> 2. Atualização do `hash_content`
> 3. Novo provenance

### Encerramento

> Nunca DELETE. Setar `valid_to = now()` + event `anulacao` com razão.

### Convenções de payload por type

> A estrutura do payload é definida por convenção per type_slug. Validação é responsabilidade do pipeline, não do schema. Futuras versões podem introduzir schemas de validação por type.

#### Payload obrigatório por type (ground zero):

| type_slug | campos obrigatórios no payload |
|---|---|
| constituicao | `title`, `jurisdiction`, `promulgation_date` |
| artigo | `text_content`, `sibling_order` |
| inciso | `text_content`, `sibling_order` |
| paragrafo | `text_content`, `sibling_order` |
| alinea | `text_content`, `sibling_order` |
| caput | `text_content` |
| titulo | `text_content`, `sibling_order`, `numero_romano` |
| capitulo | `text_content`, `sibling_order`, `numero_romano` |
| secao | `text_content`, `sibling_order`, `numero_romano` |
| acao_direta | `process_number`, `court`, `class_code` |
| recurso_extraordinario | `process_number`, `court`, `class_code` |
| sumula_vinculante | `numero`, `enunciado` |
| emenda_constitucional | `numero`, `data`, `ementa` |
| subject | `label` |
| anotacao | `text`, `annotation_type` |
| versao_normativa | `label`, `trigger_description` |

> Campos derivados/cache no payload (recalculáveis):
> `path_slug`, `depth_level`, `is_leaf`, `is_repealed`, `normalized_text`

> Fonte de verdade no payload (não deriváveis):
> `text_content`, `sibling_order`, `numero_romano`

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

> Sucessão via edge `sucede`. Não existe campo `succession_slug`.
> Ciclo de vida via events com `aggregate_slug = actor.slug`.
> Actor `sistema-pipeline` é autor de events automatizados.

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

> `aggregate_slug` aponta para **objects ou actors**.
> `actor_slug` é **NOT NULL**. Usar `sistema-pipeline` para events automatizados.
> `causation_id` encadeia events: "este julgamento causou esta mudança de estado".

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

> Para edge_types com `allows_multiple = false`: máximo um edge ativo (valid_to IS NULL) por par type+source+target.
> Encerrar edge: setar `valid_to = now()`. Nunca DELETE.

## 6.5 Unicidade global de slugs

> Slugs são **globalmente únicos** entre objects e actors. Garantido pela convenção:

| Primitivo | Padrão | Exemplo |
|---|---|---|
| object normativo (corpo CF) | (obra)-art-(n) | `cf-1988-art-5` |
| object normativo (ADCT) | (obra)-adct-art-(n) | `cf-1988-adct-art-1` |
| object jurídico | (tribunal)-(classe)-(número) | `stf-adi-4650` |
| object subject | subject-(tema) | `subject-saude` |
| object anotação | anotacao-(contexto) | `anotacao-cf1988-art5-ec45` |
| object emenda | cf-ec-(número) | `cf-ec-45` |
| object versão | (obra)-v-(referência) | `cf-1988-v-ec45` |
| actor | (papel)-(nome) | `ministro-barroso` |
| actor sistema | sistema-(nome) | `sistema-pipeline` |

> Events usam `event_id` (uuid). Edges usam `edge_id` (uuid). Sem colisão com slugs.

## 6.6 Três tempos irredutíveis

| Primitivo | occurred_at | valid_from/to | recorded_at |
|---|---|---|---|
| objects | — | sim | sim |
| actors | — | sim | sim |
| events | sim | — | sim |
| edges | — | sim | sim |

* **occurred_at** — quando aconteceu no mundo real (só events)
* **valid_from / valid_to** — período de vigência (objects, actors, edges)
* **recorded_at** — quando o sistema registrou (todos)

## 6.7 Regra

> Toda entidade especializada é instância de um destes quatro.
> `constituicao` = object. `ministro` = actor. `julgamento` = event. `interpreta` = edge. `anotacao` = object.

---

# 7. VERSIONAMENTO DE OBRAS NORMATIVAS

## 7.1 Princípio

> Versionamento é **event-sourced**. Nós são modificados in-place. O histórico é reconstruído via events. A versão é um marco temporal, não uma cópia.

## 7.2 Como funciona uma emenda

Quando a EC 45/2004 adiciona § 3º ao Art. 5º:

```
1. INSERT object: cf-ec-45 (type: emenda_constitucional)
   payload: { numero: 45, data: "2004-12-30", ementa: "Reforma do Judiciário" }

2. INSERT object: cf-1988-art-5-par-3 (type: paragrafo)
   payload: { text_content: "Os tratados e convenções...", sibling_order: 3 }

3. INSERT edge: cf-1988-art-5 --[parent_of]--> cf-1988-art-5-par-3

4. INSERT edge: cf-ec-45 --[amends]--> cf-1988-art-5

5. INSERT event: emenda_aplicada
   aggregate_slug: cf-1988-art-5
   payload: {
     emenda: "cf-ec-45",
     action: "adicionou_paragrafo",
     node_adicionado: "cf-1988-art-5-par-3"
   }
   occurred_at: 2004-12-30

6. INSERT object: cf-1988-v-ec45 (type: versao_normativa)
   payload: { label: "CF pós-EC 45", trigger_description: "Reforma do Judiciário" }

7. INSERT edge: cf-1988-v-ec45 --[version_of]--> cf-1988
```

## 7.3 Reconstrução temporal

> Para saber como a CF estava em uma data X:
> 1. Buscar todos os objects do tipo normativo com `valid_from <= X` e (`valid_to IS NULL` ou `valid_to > X`)
> 2. Buscar todos os events com `occurred_at <= X` para reconstruir estados
> 3. Os edges `parent_of` ativos naquela data definem a árvore

## 7.4 Regras

> Nunca duplicar a árvore inteira para cada versão.
> A versão é um **object marcador** com edge `version_of` → obra.
> As alterações são events sobre os nós afetados.
> O edge `amends` liga a emenda aos nós que ela alterou.

---

# 8. EQUIVALÊNCIA v1 → v6

| v1 | v6 | Como |
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

---

# 9. ÁRVORE UNIVERSAL

## 9.1 Definição

Árvore = edges `parent_of` entre objects. Não existe tabela de nós.

## 9.2 Tipos de nó (domain: normativo)

* livro, parte, título, capítulo, seção, subseção
* artigo, caput, parágrafo, inciso, alínea, item, anexo

## 9.3 Fonte de verdade e cache

| Campo no payload | Natureza |
|---|---|
| `text_content` | fonte de verdade |
| `sibling_order` | fonte de verdade |
| `numero_romano` | fonte de verdade |
| `path_slug` | cache (derivado dos edges) |
| `depth_level` | cache (derivado) |
| `is_leaf` | cache (derivado) |
| `is_repealed` | cache (derivado do último event de estado) |
| `normalized_text` | cache (derivado de text_content) |

> Se cache divergir de edge/event, edge/event vence.

## 9.4 Regras

> Nenhum nó sem edge `parent_of` (exceto raiz).
> Edges `parent_of` só entre objects do mesmo domínio ou sub-grafo.
> Queries sobre árvore filtram por domain_slug.

---

# 10. SUBJECTS (TEMAS)

## 10.1 Definição

Objects do type `subject` (domain: `transversal`). Hierarquia via `parent_of`. Vinculação via edge `sobre`.

## 10.2 Exemplos

```
subject-saude --[parent_of]--> subject-saude-publica
stf-adi-4650 --[sobre]--> subject-financiamento-eleitoral
cf-1988-art-196 --[sobre]--> subject-saude
```

## 10.3 Regras

> Subject é object. Vincula-se por edge. Um object pode ter múltiplos subjects.

---

# 11. ANOTAÇÕES

Objects do type `anotacao` (domain: `transversal`). Vinculação via edge `annota` ao nó mais específico.

> Anotação é object, não event. Pode ser corrigida (mutação com rastreio).

---

# 12. PAPÉIS (ROLES)

Edge `exerce_papel` entre actor e object/contexto, com `{role: "relator"}` no payload.

> Papel não é tabela. É edge tipado com especificação no payload.

---

# 13. CONVENÇÃO DE SLUG

## 13.1 Princípios

* determinística, estável, legível, independente de contexto
* **globalmente única entre objects e actors**
* **nunca muda depois de criada**

## 13.2 Formato completo

| Categoria | Padrão | Exemplo |
|---|---|---|
| constituição | cf-(ano) | `cf-1988` |
| versão | (obra)-v-(ref) | `cf-1988-v-ec45` |
| emenda | cf-ec-(n) | `cf-ec-45` |
| título | (obra)-tit-(n) | `cf-1988-tit-2` |
| capítulo | (obra)-tit-N-cap-(n) | `cf-1988-tit-2-cap-1` |
| seção | ...-sec-(n) | `cf-1988-tit-2-cap-1-sec-1` |
| artigo (corpo) | (obra)-art-(n) | `cf-1988-art-5` |
| artigo (ADCT) | (obra)-adct-art-(n) | `cf-1988-adct-art-1` |
| caput | (obra)-art-N-caput | `cf-1988-art-5-caput` |
| inciso | (obra)-art-N-inc-(rom) | `cf-1988-art-5-inc-ix` |
| alínea | ...-ali-(letra) | `cf-1988-art-5-inc-ix-ali-a` |
| parágrafo | (obra)-art-N-par-(n) | `cf-1988-art-5-par-1` |
| decisão | (tribunal)-(classe)-(número) | `stf-adi-4650` |
| súmula | (tribunal)-sv-(número) | `stf-sv-11` |
| subject | subject-(tema) | `subject-saude` |
| anotação | anotacao-(contexto) | `anotacao-cf1988-art5-ec45` |
| actor humano | (papel)-(nome) | `ministro-barroso` |
| actor sistema | sistema-(nome) | `sistema-pipeline` |

## 13.3 Path (cache derivado)

```text
cf-1988/tit-2/cap-1/art-5/inc-ix
cf-1988/adct/art-1
```

## 13.4 Regras

> Slug identifica o objeto. Path identifica a posição.
> Slug nunca muda. Dois primitivos nunca compartilham slug.
> ADCT usa prefixo `adct` para evitar colisão com corpo principal.

---

# 14. CAMADA 3 — PROVENANCE

## 14.1 Estrutura

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

> `target_slug` para objects/actors = slug. Para events = event_id. Para edges = edge_id.
> `target_table`: `objects`, `actors`, `events`, `edges`.

## 14.2 source_types

* `manual` — humano
* `scraping` — fonte web
* `parsing` — documento (PDF, DOCX, HTML)
* `pipeline` — transformação automática
* `ia` — modelo de linguagem

## 14.3 Regras

> Nenhum dado sem provenance. Reprocessar via hash_input. Confidence ordena conflitos.

---

# 15. CAMADA 4 — DERIVADOS

Reconstruíveis. Nunca base primária.

```
chunks
  chunk_slug            text PK
  object_slug           text NOT NULL
  chunk_text            text NOT NULL
  chunk_index           integer NOT NULL
  token_estimate        integer
  hash_chunk            text

embeddings
  chunk_slug            text FK → chunks
  embedding_model       text NOT NULL
  vector_ref            vector(1536)
  created_at            timestamptz DEFAULT now()
  UNIQUE (chunk_slug, embedding_model)

published_objects
  slug                  text PK
  payload_json          jsonb NOT NULL
  payload_hash          text NOT NULL
  updated_at            timestamptz DEFAULT now()
```

> Embedding nunca substitui estrutura. JSON nunca é base primária.

---

# 16. CAMADA 5 — PADRÕES E VIEWS

## 16.1 Views essenciais

```sql
v_objects_with_domain
  slug, type_slug, domain_slug, payload, valid_from, valid_to

v_current_state
  slug, type_slug, domain_slug, current_state, last_event_at

v_tree_nodes
  slug, type_slug, parent_slug, path_slug, depth_level,
  sibling_order, domain_slug

v_decidability_index
  node_slug, domain_slug, edge_count_by_type, total_edges
```

> Views são recalculáveis. Não são fonte de verdade. Incluem domain_slug denormalizado.

---

# 17. IDENTIDADE MULTINÍVEL

| Nível | Campo | Função |
|---|---|---|
| identidade | slug (globalmente único) | quem é |
| domínio | type_slug → domain_slug | a que sistema pertence |
| versão | hash_content | em que estado está |
| estado | último event com to_state | situação no ciclo de vida |
| tema | edges tipo `sobre` | de que assunto trata |
| papel | edges tipo `exerce_papel` | função exercida |
| granularidade | chunk_slug | busca semântica |
| posição | path_slug (cache) | onde está na árvore |
| origem | provenance_id | de onde veio |

---

# 18. REGRAS DE VÍNCULO

1. Vincular ao nó mais específico
2. Nunca colapsar no caput
3. Subir por agregação
4. Registrar incerteza (confidence no provenance)
5. Separar vínculo inferido de vínculo confirmado (source_type no provenance)

---

# 19. OPERAÇÕES SOBRE DADOS

| Operação | Como | Obrigatório |
|---|---|---|
| **Criar** | INSERT primitivo + INSERT provenance | provenance |
| **Corrigir** | UPDATE payload + event `correcao` + novo provenance | event + provenance |
| **Encerrar** | SET valid_to + event `anulacao` | event |
| **Relacionar** | INSERT edge + provenance | provenance |
| **Mudar estado** | INSERT event com `to_state` | event |
| **Versionar obra** | INSERT versao_normativa + events nos nós | events |

> Nunca DELETE. Nunca UPDATE sem event. Nunca INSERT sem provenance.

---

# 20. ÍNDICES RECOMENDADOS

```
-- Primitivos
objects:     (type_slug), (valid_from), (valid_to)
actors:      (type_slug), (valid_from)
events:      (aggregate_slug, occurred_at), (type_slug), (actor_slug)
edges:       (type_slug, source_slug), (type_slug, target_slug),
             (source_slug), (target_slug)

-- JSONB (para queries de payload)
edges:       GIN (payload)
events:      GIN (payload)

-- Provenance
provenance:  (target_slug, target_table)
```

---

# 21. ESCALABILIDADE

## Chaves estruturais

* `domain_slug` (via type)
* `type_slug`
* `slug`
* `valid_from` / `valid_to`

## Estratégia

* rebuild parcial por domínio
* reindexação por hash
* chunking incremental
* embeddings sob demanda
* expansão por INSERT em domains + types

---

# 22. BUSCA

## 22.1 Lexical
* filtros por domínio, type, subject, período

## 22.2 Semântica
* similaridade via embeddings

## 22.3 Híbrida
* filtro + ranking semântico

---

# 23. PIPELINE

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
11. materialização de views
12. publicação (published_objects)

---

# 24. ERROS PROIBIDOS

* colapsar estrutura
* modelar por tela
* usar slug como única estrutura
* misturar camadas
* embeddar antes de estruturar
* perder vínculo com fonte
* **hardcodar quantidade de domínios**
* **tratar zona de integração como camada fixa**
* **inserir dado sem provenance**
* **criar tabela para entidade que cabe nos 4 primitivos**
* **armazenar estado como campo — estado é derivado de events**
* **usar campo para tema — tema é object vinculado por edge**
* **reutilizar slug entre tabelas**
* **tratar payload como fonte de verdade para relações — edges vencem**
* **usar DELETE — encerrar com valid_to + event**
* **criar event sem actor — usar sistema-pipeline**
* **modelar relação como campo — relação é edge**
* **duplicar árvore inteira para versionar — versão é marco, não cópia**

---

# 25. FÓRMULA DE EXPANSÃO

```text
1. INSERT em domains (novo sistema)
2. INSERT em *_types com domain_slug (vocabulário)
3. INSERT em state_types (estados possíveis)
4. INSERT em objects · actors · events · edges (fatos)
5. INSERT em provenance (origem)
6. Materializar views
7. Derivados se recalculam

Nunca ALTER TABLE. Nunca redesenho. Nunca partir do zero.
```

---

# 26. FÓRMULA FINAL

```text
DOMAINS (N, hierárquicos, inclui transversal)
→ TAXONOMIAS (object_types · actor_types · event_types · edge_types · state_types)
→ PRIMITIVOS (objects · actors · events · edges)
→ PROVENANCE (rastreabilidade)
→ VIEWS MATERIALIZADAS (domain, estado, árvore, decidibilidade)
→ DERIVADOS (chunks · embeddings · JSON)
→ API / VIEWS
```

---

# 27. PRINCÍPIO FINAL

> O sistema não organiza textos.
> Ele organiza relações estruturadas entre textos, decisões, normas e instituições, em múltiplos domínios e escalas.
> O átomo de hoje é a cartografia do contencioso constitucional.
> O cosmos de amanhã é INSERT.

---

**Este protocolo define a arquitetura permanente do sistema.
Nenhuma implementação deve violar suas regras estruturais.**

**v6 — 25 de março de 2026**
**Damares Medina**
