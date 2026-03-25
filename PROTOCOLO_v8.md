# PROTOCOLO ONTOLÓGICO UNIVERSAL v8

## Cartografia do Litigioso Brasileiro

---

# 1. ÂNCORA E FINALIDADE

**Autora:** Damares Medina
**Objeto:** Cartografia do litigioso brasileiro
**Princípio:** O sistema modela **relações entre estruturas normativas, documentos jurídicos, atores institucionais e argumentos**, em múltiplos domínios e escalas.

---

# 2. PRINCÍPIOS INEGOCIÁVEIS

1. Todo corpus jurídico é uma **árvore multinível**
2. O artigo **não é a raiz** da estrutura normativa
3. Todo objeto possui **identidade estável (slug)**
4. Estrutura ≠ texto ≠ derivação
5. Embeddings são **derivados, nunca estruturais**
6. A base é **corpus-agnóstica e hierarquia-aware**
7. Nenhuma camada depende do frontend
8. **Domínios são dados, não estrutura** — crescem por INSERT
9. **Cross-edges são consequência** — edge entre domínios diferentes = cross-edge
10. **Toda informação tem origem rastreável** — provenance obrigatório
11. **Existem apenas 4 primitivos** — object, actor, event, edge. Sem exceções
12. **Estado é derivado** — último event com `to_state`
13. **Temas são objects** — vinculados por edges, não campos
14. **Slugs são globalmente únicos** — nenhum slug em mais de uma tabela
15. **Edge é fonte de verdade para relações** — payload é cache derivado
16. **Nunca DELETE** — encerrar com `valid_to` + event `anulacao`
17. **source [verbo] target** — direção universal dos edges
18. **Versionamento event-sourced** — nós in-place, versão é marco
19. **Payload é convenção** — estrutura por type, validação no pipeline
20. **UUID é identidade interna irredutível** — slug é identidade pública legível. Relações estruturais ancoram-se em UUID; slugs servem à leitura, publicação e interoperabilidade humana
21. **Domain ≠ classe ontológica** — domínio indica pertencimento institucional; classe indica a natureza do ente modelado
22. **Cada tipo de relação tem classe epistêmica** — distinguir fato estrutural de interpretação de classificação
23. **O sistema registra sinais, não apenas fatos** — toda decisão deve conter o sinal decisório mínimo necessário para reconstruir e projetar padrões de desfecho, direção, fundamentação, técnica decisória e efeito material
24. **Predição é função da camada analítica** — construída sobre types, payloads, edges, events e views, nunca sobre os primitivos

---

# 3. ARQUITETURA EM CAMADAS

```text
CAMADA 0 — DOMÍNIOS
  domains (hierárquicos, expansíveis)

CAMADA 1 — TAXONOMIAS VIVAS
  object_types (+ ontological_class)
  actor_types (+ actor_class)
  event_types (+ event_class)
  edge_types (+ epistemic_class)
  state_types
  (domain_slug nullable para transversais)

CAMADA 2 — PRIMITIVOS UNIVERSAIS (schema fixo)
  objects (id uuid + slug)
  actors (id uuid + slug)
  events (referencia por uuid)
  edges (source_id/target_id uuid)

CAMADA 3 — PROVENANCE (rastreabilidade)
  provenance (cruza tudo, referencia por uuid)

CAMADA 4 — DERIVADOS (reconstruíveis)
  chunks · embeddings · published_objects

CAMADA 5 — PADRÕES (views materializadas)
  domain denormalizado, slugs resolvidos, estado atual
```

---

# 4. CAMADA 0 — DOMÍNIOS

## 4.1 Definição

Um domínio é um **sistema institucional autônomo**. Domínios são dados — entram por INSERT.

## 4.2 Estrutura

```
domains
  domain_slug           text PK
  label                 text NOT NULL
  parent_domain_slug    text FK → domains (nullable)
  valid_from            timestamptz
```

## 4.3 Hierarquia

```text
transversal
normativo
juridico
  └── stf · stj · tst
executivo
  └── presidencia · agu · pgfn
mp
  └── pgr · mpf
legislativo
  └── senado · camara
controle
  └── tcu · cnj
```

## 4.4 Ground zero

3 domínios: `transversal`, `normativo`, `juridico`.

## 4.5 Regra

> Nunca hardcodar quantidade de domínios. Funciona com 2 ou 200.

---

# 5. CAMADA 1 — TAXONOMIAS VIVAS

Dados, nunca enums. Crescem por INSERT. `domain_slug` nullable para transversais.

## 5.1 `object_types`

```
object_types
  type_slug             text PK
  domain_slug           text FK → domains (nullable)
  ontological_class     text NOT NULL
  label                 text
  valid_from            timestamptz
```

> `domain_slug` responde: **a que sistema pertence**
> `ontological_class` responde: **o que é**

Classes ontológicas:

| Classe | Significado |
|---|---|
| estrutural | entidade estática com existência própria (norma, dispositivo, súmula) |
| processual | entidade dinâmica com ciclo de vida (ação, recurso, processo) |
| semantico | entidade abstrata classificatória (tema, assunto) |
| editorial | entidade derivada de intervenção humana (anotação, comentário) |
| argumentativo | entidade que expressa razão, tese ou fundamento |
| analitico | entidade de análise quantitativa ou qualitativa derivada (impacto, estimativa) |
| preditivo | entidade que captura sinal decisório para projeção de padrões |

Exemplos:

| type_slug | domain | ontological_class | label |
|---|---|---|---|
| constituicao | normativo | estrutural | Constituição |
| versao_normativa | normativo | estrutural | Versão/marco temporal |
| emenda_constitucional | normativo | estrutural | Emenda Constitucional |
| titulo | normativo | estrutural | Título |
| capitulo | normativo | estrutural | Capítulo |
| secao | normativo | estrutural | Seção |
| artigo | normativo | estrutural | Artigo |
| caput | normativo | estrutural | Caput |
| inciso | normativo | estrutural | Inciso |
| paragrafo | normativo | estrutural | Parágrafo |
| alinea | normativo | estrutural | Alínea |
| acao_direta | juridico | processual | Ação Direta |
| recurso_extraordinario | juridico | processual | Recurso Extraordinário |
| sumula_vinculante | juridico | estrutural | Súmula Vinculante |
| decreto | executivo | estrutural | Decreto |
| projeto_lei | legislativo | processual | Projeto de Lei |
| subject | transversal | semantico | Tema/assunto |
| anotacao | transversal | editorial | Anotação editorial |
| argumento | juridico | argumentativo | Razão de decidir / fundamento |
| impacto_orcamentario | transversal | analitico | Impacto orçamentário de decisão |
| estimativa_fiscal | transversal | analitico | Estimativa fiscal quantificada |
| nota_tecnica_fiscal | transversal | editorial | Nota técnica sobre impacto fiscal |
| resultado_decisorio | juridico | preditivo | Sinal de resultado de julgamento |
| fundamento | juridico | argumentativo | Fundamento jurídico |
| tese | juridico | argumentativo | Tese fixada ou proposta |

## 5.2 `actor_types`

```
actor_types
  type_slug             text PK
  domain_slug           text FK → domains (nullable)
  actor_class           text NOT NULL
  label                 text
  valid_from            timestamptz
```

Classes de actor:

| Classe | Significado |
|---|---|
| institucional | ator investido de função pública |
| automatizado | ator de sistema (pipeline, IA) |

Exemplos:

| type_slug | domain | actor_class | label |
|---|---|---|---|
| ministro_stf | juridico | institucional | Ministro do STF |
| presidente | executivo | institucional | Presidente da República |
| procurador_geral | mp | institucional | Procurador-Geral |
| senador | legislativo | institucional | Senador |
| deputado | legislativo | institucional | Deputado Federal |
| sistema | transversal | automatizado | Ator automatizado |

## 5.3 `event_types`

```
event_types
  type_slug             text PK
  domain_slug           text FK → domains (nullable)
  event_class           text NOT NULL
  label                 text
  valid_from            timestamptz
```

Classes de event:

| Classe | Significado |
|---|---|
| juridico | ocorrência do sistema de justiça |
| normativo | ocorrência do sistema normativo |
| manutencao | ocorrência operacional do sistema |
| fiscal | ocorrência com consequência orçamentária/fiscal |

Exemplos:

| type_slug | domain | event_class | label |
|---|---|---|---|
| julgamento | juridico | juridico | Julgamento |
| distribuicao | juridico | juridico | Distribuição |
| publicacao_dje | juridico | juridico | Publicação no DJe |
| promulgacao | normativo | normativo | Promulgação |
| emenda_aplicada | normativo | normativo | Aplicação de emenda |
| nomeacao | executivo | juridico | Nomeação |
| mudanca_estado | transversal | manutencao | Transição de estado |
| correcao | transversal | manutencao | Correção de dado |
| anulacao | transversal | manutencao | Anulação de dado |
| criacao | transversal | manutencao | Registro de criação |
| alocacao_risco_fiscal | juridico | fiscal | Redistribuição de risco fiscal |
| modulacao_efeitos_fiscais | juridico | fiscal | Modulação de efeitos com impacto fiscal |
| formacao_resultado | juridico | juridico | Formação de resultado decisório |

## 5.4 `edge_types`

```
edge_types
  type_slug             text PK
  source_domain_slug    text FK → domains (nullable)
  target_domain_slug    text FK → domains (nullable)
  epistemic_class       text NOT NULL
  label                 text
  bidirectional         boolean DEFAULT false
  allows_multiple       boolean DEFAULT true
  weight_semantics      text
  weight_required       boolean DEFAULT false
  valid_from            timestamptz
```

Classes epistêmicas:

| Classe | Significado | Exemplo |
|---|---|---|
| estrutural | relação constitutiva da árvore/hierarquia | parent_of, version_of |
| normativa | relação que altera o ordenamento | amends, emenda, veta |
| interpretativa | relação hermenêutica entre decisão e norma | interpreta, aplica, questiona |
| classificatoria | relação taxonômica/temática | sobre |
| editorial | relação de anotação/comentário | annota |
| institucional | relação entre atores e funções | exerce_papel, sucede, nomeia, denuncia |
| argumentativa | relação entre fundamentos e decisões | suporta, contradiz, fundamenta, apoia, confirma, supera |
| fiscal | relação de impacto orçamentário/fiscal | impacta_orcamento, aloca_risco_fiscal, modula |
| preditiva | relação que captura sinal de desfecho | decide_em_favor_de |

Exemplos:

| type_slug | source | target | epistemic | mult | weight_semantics | weight_req | label |
|---|---|---|---|---|---|---|---|
| parent_of | NULL | NULL | estrutural | false | NULL | false | relação hierárquica |
| version_of | normativo | normativo | estrutural | false | NULL | false | versão de obra |
| amends | normativo | normativo | normativa | true | NULL | false | emenda altera dispositivo |
| emenda | legislativo | normativo | normativa | true | NULL | false | emenda constituição |
| veta | executivo | legislativo | normativa | false | NULL | false | veta projeto |
| interpreta | juridico | normativo | interpretativa | true | confidence (0-1) | true | interpreta dispositivo |
| aplica | juridico | normativo | interpretativa | true | confidence (0-1) | true | aplica norma |
| questiona | juridico | normativo | interpretativa | true | confidence (0-1) | true | questiona constitucionalidade |
| sobre | NULL | NULL | classificatoria | true | relevancia (0-1) | false | vincula a tema |
| annota | NULL | NULL | editorial | true | NULL | false | anotação ao alvo |
| exerce_papel | NULL | NULL | institucional | true | NULL | false | papel no contexto |
| sucede | NULL | NULL | institucional | false | NULL | false | sucessão de actor |
| relator_de | juridico | juridico | institucional | false | NULL | false | relator do processo |
| nomeia_ministro | executivo | juridico | institucional | false | NULL | false | nomeia ministro |
| denuncia | mp | juridico | institucional | true | NULL | false | oferece denúncia |
| suporta | juridico | juridico | argumentativa | true | forca (0-1) | false | fundamento suporta decisão |
| contradiz | juridico | juridico | argumentativa | true | forca (0-1) | false | argumento contradiz argumento |
| fundamenta_em | juridico | normativo | argumentativa | true | confidence (0-1) | false | argumento se fundamenta em norma |
| impacta_orcamento | juridico | NULL | fiscal | true | magnitude (0-1) | true | decisão impacta orçamento de ente |
| aloca_risco_fiscal | juridico | NULL | fiscal | true | magnitude (0-1) | true | decisão redistribui risco fiscal |
| quantifica | NULL | NULL | fiscal | true | confidence (0-1) | false | vincula estimativa a impacto |
| mitiga_impacto | juridico | juridico | fiscal | true | eficacia (0-1) | false | modulação mitiga impacto fiscal |
| externaliza_risco | juridico | NULL | fiscal | true | magnitude (0-1) | false | decisão transfere risco a terceiro |
| decide_em_favor_de | juridico | NULL | preditiva | true | confidence (0-1) | false | decisão favorece parte/ente |
| fundamenta | juridico | juridico | argumentativa | true | forca (0-1) | false | fundamento embasa decisão |
| apoia | juridico | juridico | argumentativa | true | forca (0-1) | false | fundamento/tese apoia outro |
| confirma | juridico | juridico | argumentativa | true | confidence (0-1) | false | decisão confirma precedente |
| supera | juridico | juridico | argumentativa | true | confidence (0-1) | false | decisão supera precedente |
| modula | juridico | juridico | fiscal | true | eficacia (0-1) | false | decisão modula efeitos |
| gera_impacto_orcamentario | juridico | NULL | fiscal | true | magnitude (0-1) | false | decisão gera impacto orçamentário |

> `weight_semantics` declara o que o weight significa para cada tipo.
> `weight_required` indica se o weight é obrigatório na inserção.

### Regras

> **source [verbo] target** — sempre.
> Mesmo domínio = interna. Diferente = cross-edge. NULL = transversal.
> `allows_multiple = false`: máx 1 edge ativo por type+source+target.
> `epistemic_class` permite filtrar por natureza da relação: separar fato de interpretação de classificação.

## 5.5 `state_types`

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

Exemplos:

| state | object_type | domain | terminal |
|---|---|---|---|
| vigente | artigo | normativo | false |
| vigente | inciso | normativo | false |
| vigente | paragrafo | normativo | false |
| suspensa | artigo | normativo | false |
| revogada | artigo | normativo | true |
| distribuida | acao_direta | juridico | false |
| pautada | acao_direta | juridico | false |
| julgada | acao_direta | juridico | false |
| transitada | acao_direta | juridico | true |

> Estado = último event com `to_state`, ordenado por `occurred_at`.
> `aggregate_slug` aponta para objects ou actors.

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

> **UUID é identidade interna irredutível. Slug é identidade pública legível.**
> Relações estruturais ancoram-se em UUID. Slugs servem à leitura, publicação e interoperabilidade humana.

## 6.1 `objects`

```
objects
  id            uuid PK DEFAULT gen_random_uuid()
  slug          text UNIQUE NOT NULL
  type_slug     text FK → object_types
  payload       jsonb
  hash_content  text
  valid_from    timestamptz
  valid_to      timestamptz (nullable)
  recorded_at   timestamptz DEFAULT now()
```

### Mutabilidade

> Mutáveis com rastreio. Toda mutação gera:
> 1. Event `correcao` com `hash_anterior` no payload
> 2. Atualização do `hash_content`
> 3. Novo provenance

### Encerramento

> `valid_to = now()` + event `anulacao`. Nunca DELETE.

### Payload obrigatório por type (ground zero)

| type_slug | campos obrigatórios |
|---|---|
| constituicao | `title`, `jurisdiction`, `promulgation_date` |
| artigo | `text_content`, `sibling_order` |
| inciso | `text_content`, `sibling_order` |
| paragrafo | `text_content`, `sibling_order` |
| alinea | `text_content`, `sibling_order` |
| caput | `text_content` |
| titulo | `text_content`, `sibling_order`, `numero_romano` |
| acao_direta | `process_number`, `court`, `class_code` |
| sumula_vinculante | `numero`, `enunciado` |
| emenda_constitucional | `numero`, `data`, `ementa` |
| subject | `label` |
| anotacao | `text`, `annotation_type` |
| argumento | `text_content`, `argument_type` |
| resultado_decisorio | `outcome`, `outcome_polarity`, `decision_unanimity`, `merits_reached` |
| fundamento | `text_content`, `fundamento_type` |
| tese | `text_content`, `binding`, `fixation_date`, `status` |
| impacto_orcamentario | `decisao_slug`, `ente_afetado`, `direcao`, `horizonte_temporal` |
| estimativa_fiscal | `valor_brl`, `metodologia`, `fonte`, `data_referencia`, `confianca` |
| nota_tecnica_fiscal | `text`, `autor`, `annotation_type` |

> Fonte de verdade no payload: `text_content`, `sibling_order`, `numero_romano`
> Cache derivável: `path_slug`, `depth_level`, `is_leaf`, `is_repealed`, `normalized_text`

## 6.2 `actors`

```
actors
  id            uuid PK DEFAULT gen_random_uuid()
  slug          text UNIQUE NOT NULL
  type_slug     text FK → actor_types
  payload       jsonb
  dedup_hash    text
  valid_from    timestamptz
  valid_to      timestamptz (nullable)
  recorded_at   timestamptz DEFAULT now()
```

> Sucessão via edge `sucede`. Ciclo de vida via events.
> Actor `sistema-pipeline` é autor de events automatizados.

## 6.3 `events`

Append-only. Imutável. Nunca UPDATE, nunca DELETE.

```
events
  event_id        uuid PK DEFAULT gen_random_uuid()
  type_slug       text FK → event_types
  aggregate_id    uuid NOT NULL
  actor_id        uuid NOT NULL
  payload         jsonb
  causation_id    uuid FK → events (nullable)
  occurred_at     timestamptz NOT NULL
  recorded_at     timestamptz DEFAULT now()
```

> `aggregate_id` aponta para objects.id ou actors.id.
> `actor_id` aponta para actors.id. NOT NULL — usar `sistema-pipeline`.
> `causation_id` encadeia events.

## 6.4 `edges`

Grafo tipado universal.

```
edges
  edge_id              uuid PK DEFAULT gen_random_uuid()
  type_slug            text FK → edge_types
  source_id            uuid NOT NULL
  target_id            uuid NOT NULL
  weight               float (nullable)
  payload              jsonb (nullable)
  valid_from           timestamptz (nullable)
  valid_to             timestamptz (nullable)
  causation_event_id   uuid FK → events (nullable)
  recorded_at          timestamptz DEFAULT now()
```

> `source_id` e `target_id` são uuid — fonte de verdade relacional.
> Slugs resolvidos via views (v_edges_readable).
> `allows_multiple = false`: máx 1 edge ativo por type+source+target.
> Encerrar: `valid_to = now()`. Nunca DELETE.
> `weight` obrigatório quando `edge_type.weight_required = true`.

## 6.5 Identidade dual

| Camada | Campo | Função |
|---|---|---|
| interna | `id` (uuid) | identidade irredutível, FK, consistência |
| pública | `slug` (text) | identidade legível, publicação, API |

> UUID garante consistência. Slug garante inteligibilidade.
> Relações (edges, events) ancoram em UUID.
> Interfaces humanas (API, views, export) expõem slugs.

## 6.6 Três tempos irredutíveis

| Primitivo | occurred_at | valid_from/to | recorded_at |
|---|---|---|---|
| objects | — | sim | sim |
| actors | — | sim | sim |
| events | sim | — | sim |
| edges | — | sim | sim |

## 6.7 Regra

> Toda entidade é instância de um destes quatro.
> `constituicao` = object. `ministro` = actor. `julgamento` = event. `interpreta` = edge. `argumento` = object.

---

# 7. ARGUMENTOS

## 7.1 Definição

Argumentos são **objects** do type `argumento` (ontological_class: `argumentativo`). Representam razões de decidir, teses, fundamentos e dissensos dentro de decisões.

## 7.2 Estrutura

```
object: arg-adi4650-financiamento-privado
  type: argumento
  payload: {
    text_content: "O financiamento privado de campanhas compromete a igualdade...",
    argument_type: "razao_decidir",
    direction: "procedente"
  }
```

## 7.3 Tipos de argumento (via payload `argument_type`)

* `razao_decidir` — fundamento principal da decisão
* `obiter_dictum` — consideração acessória
* `voto_divergente` — fundamento do dissenso
* `tese_fixada` — tese de repercussão geral

## 7.4 Vinculação

```
arg-adi4650-financiamento-privado --[suporta]--> stf-adi-4650
arg-adi4650-financiamento-privado --[fundamenta_em]--> cf-1988-art-1
arg-adi4650-financiamento-privado --[fundamenta_em]--> cf-1988-art-5

arg-adi4650-liberdade-expressao --[contradiz]--> arg-adi4650-financiamento-privado
arg-adi4650-liberdade-expressao --[suporta]--> stf-adi-4650
  payload: { role: "voto_divergente", ministro: "ministro-gilmar" }
```

## 7.5 Regras

> Argumento é object, não event. Tem existência própria e pode ser referenciado por múltiplas decisões.
> `suporta` liga argumento à decisão. `fundamenta_em` liga argumento à norma.
> `contradiz` liga argumento a argumento — captura dissenso interno.
> Isso transforma o sistema em máquina de análise argumentativa, não apenas banco de decisões.

---

# 8. SINAIS DECISÓRIOS (CAMADA PROSPECTIVA)

## 8.1 Princípio

> O sistema não deve apenas registrar que houve decisão; deve registrar o sinal decisório mínimo necessário para reconstruir e projetar padrões de desfecho, direção, fundamentação, técnica decisória e efeito material.

> Predição não é função dos primitivos; é função da camada analítica construída sobre types, payloads, edges, events e views.

## 8.2 Camada de resultado

Payload padronizado obrigatório no event_type `julgamento`:

```json
{
  "outcome": "procedente | improcedente | parcial | nao_conhecido | prejudicado",
  "outcome_polarity": "favor_autor | favor_reu | favor_estado | favor_particular | misto",
  "decision_unanimity": "unanime | maioria | monocratica",
  "merits_reached": true
}
```

Ou, para máxima granularidade, criar object_type `resultado_decisorio` vinculado à decisão.

## 8.3 Camada de direção material

Payload no event `julgamento` ou no object `resultado_decisorio`:

```json
{
  "decision_direction": "expansiva | restritiva | conservadora | inovadora | neutra",
  "rights_effect": "amplia | restringe | preserva | indeterminado",
  "state_constraint": "aumenta | reduz | mantem"
}
```

## 8.4 Camada de técnica decisória

```json
{
  "uses_modulation": true,
  "temporal_effect": "ex_tunc | ex_nunc | prospectivo | misto",
  "injunctive_profile": "forte | medio | fraco | inexistente",
  "deference_level": "alto | medio | baixo",
  "reasoning_style": "formalista | consequencialista | principialista | pragmatica | mista"
}
```

## 8.5 Camada de fundamento

Objects tipo `fundamento` e `tese` com edges:

```
fundamento-x --[fundamenta]--> stf-adi-4650
fundamento-x --[fundamenta_em]--> cf-1988-art-14
fundamento-x --[apoia]--> tese-y

tese-rg-tema-123 --[confirma]--> tese-rg-tema-100
tese-rg-tema-200 --[supera]--> tese-rg-tema-100
```

## 8.6 Camada de efeito fiscal e institucional

Payload no event ou object analítico:

```json
{
  "fiscal_effect": "expansivo | contencao | neutro | indeterminado",
  "fiscal_risk_shift": "estado | particular | compartilhado",
  "estimated_budget_impact": 0,
  "impact_horizon": "imediato | curto | medio | longo",
  "retroactive_liability": "alta | media | baixa | inexistente"
}
```

## 8.7 Regras

> Todo julgamento deve conter no mínimo: `outcome`, `decision_direction`, `uses_modulation`, `reasoning_style`, `fiscal_effect`.
> Fundamentos e teses são objects com existência própria — podem ser referenciados por múltiplas decisões.
> A camada prospectiva não altera primitivos — apenas enriquece types, payloads, edges e views.

---

# 9. IMPACTO ORÇAMENTÁRIO

## 8.1 Definição

Impacto orçamentário é modelado em 3 níveis progressivos, sem alterar primitivos.

## 8.2 Nível 1 — Edge com payload (sempre)

Toda decisão relevante ganha um edge fiscal:

```
stf-adi-4650 --[aloca_risco_fiscal]--> ente-uniao
  payload: {
    direcao: "aumento_despesa",
    estimativa_brl: 5000000000,
    horizonte_temporal: "10_anos",
    confianca: 0.7,
    retroatividade: false,
    base_documental: "nota-tecnica-stn-2023"
  }
  weight: 0.8 (magnitude)
```

## 8.3 Nível 2 — Object analítico (quando houver material suficiente)

```
object: impacto-adi4650-financiamento
  type: impacto_orcamentario
  payload: {
    decisao_slug: "stf-adi-4650",
    ente_afetado: "uniao",
    direcao: "aumento_despesa",
    horizonte_temporal: "10_anos",
    multiplas_estimativas: [
      { fonte: "STN", valor_brl: 5000000000, data: "2023-06" },
      { fonte: "IFI", valor_brl: 3200000000, data: "2023-09" }
    ],
    divergencia_metodologica: true
  }

impacto-adi4650-financiamento --[impacta_orcamento]--> stf-adi-4650
impacto-adi4650-financiamento --[sobre]--> subject-financiamento-eleitoral
```

## 8.4 Nível 3 — Fórmulas analíticas (views derivadas)

### Exposição Fiscal Redistribuída (EFR)

```
EFR = risco_pos_decisao - risco_pre_decisao
```

Captura: quem paga após a decisão vs quem pagava antes.

### Índice de Contenção Fiscal (ICF)

```
ICF% = 1 - (impacto_efetivo / impacto_potencial)
```

Captura: quanto do impacto potencial foi contido pela modulação.

### Índice de Deslocamento Temporal (IDT)

```
IDT = data_efetividade_financeira - data_reconhecimento_juridico
```

Captura: quanto tempo entre o reconhecimento jurídico e o custo real.

### Índice de Impacto Fiscal da Decisão (IIFD)

```
IIFD = Σ(estimativas_ponderadas) × fator_retroatividade × fator_horizonte
```

### Índice de Desacoplamento Constitucional (IDC)

```
IDC = (validade_juridica_reconhecida) - (consequencia_fiscal_implementada)
```

Captura: distância entre o que o STF decidiu e o que efetivamente custou.

## 8.5 Regras

> Impacto orçamentário é modelado sem nova tabela — apenas novos types e edge_types.
> Nível 1 (edge com payload) é obrigatório para toda decisão com consequência fiscal.
> Nível 2 (object analítico) quando houver múltiplas estimativas ou divergência.
> Nível 3 (fórmulas) são views derivadas, recalculáveis.
> Edges fiscais devem ter weight obrigatório (magnitude do impacto).

---

# 10. VERSIONAMENTO

## 8.1 Princípio

> Event-sourced. Nós in-place. Histórico via events. Versão é marco, não cópia.

## 8.2 Exemplo: EC 45/2004

```
1. INSERT object: cf-ec-45 (type: emenda_constitucional)
2. INSERT object: cf-1988-art-5-par-3 (type: paragrafo)
3. INSERT edge: cf-1988-art-5 --[parent_of]--> cf-1988-art-5-par-3
4. INSERT edge: cf-ec-45 --[amends]--> cf-1988-art-5
5. INSERT event: emenda_aplicada (aggregate_id: id de cf-1988-art-5)
6. INSERT object: cf-1988-v-ec45 (type: versao_normativa)
7. INSERT edge: cf-1988-v-ec45 --[version_of]--> cf-1988
```

## 8.3 Reconstrução temporal

> CF na data X: objects com `valid_from ≤ X` e (`valid_to IS NULL` ou `valid_to > X`) + events com `occurred_at ≤ X` + edges ativos.

## 8.4 Regras

> Nunca duplicar árvore. Versão é marco. Alterações são events. Edge `amends` liga emenda aos nós.

---

# 11. EQUIVALÊNCIA v1 → v8

| v1 | v7 | Como |
|---|---|---|
| works | object | type: `constituicao` |
| work_versions | object | type: `versao_normativa` + edge `version_of` |
| legal_nodes | object | type: `artigo`, `inciso`... + edge `parent_of` |
| documents | object | type: `acao_direta`, `recurso_extraordinario` |
| annotations | object | type: `anotacao` + edge `annota` |
| citations | edge | type: `interpreta`, `aplica`, `cita` |
| node_relationships | edge | type: `parent_of`, `amends`, `revokes` |
| chunks | chunk | derivado |
| embeddings | embedding | derivado |

---

# 12. ÁRVORE UNIVERSAL

Edges `parent_of` entre objects. Sem tabela de nós.

| Campo no payload | Natureza |
|---|---|
| `text_content` | fonte de verdade |
| `sibling_order` | fonte de verdade |
| `numero_romano` | fonte de verdade |
| `path_slug` | cache |
| `depth_level` | cache |
| `is_leaf` | cache |
| `is_repealed` | cache (do último event) |
| `normalized_text` | cache |

> Cache divergiu? Edge/event vence. Nenhum nó sem `parent_of` (exceto raiz). Filtrar por domain.
> ADCT usa prefixo `adct`: `cf-1988-adct-art-1`.

---

# 13. SUBJECTS (TEMAS)

Objects type `subject` (transversal, ontological_class: semantico). Hierarquia via `parent_of`. Vinculação via edge `sobre`.

```
subject-saude --[parent_of]--> subject-saude-publica
stf-adi-4650 --[sobre]--> subject-financiamento-eleitoral
cf-1988-art-196 --[sobre]--> subject-saude
```

---

# 14. ANOTAÇÕES

Objects type `anotacao` (transversal, ontological_class: editorial). Edge `annota` ao nó mais específico.

---

# 15. PAPÉIS (ROLES)

Edge `exerce_papel` (epistemic_class: institucional) com `{role: "relator"}` no payload.

---

# 16. CONVENÇÃO DE SLUG

| Categoria | Padrão | Exemplo |
|---|---|---|
| constituição | cf-(ano) | `cf-1988` |
| versão | (obra)-v-(ref) | `cf-1988-v-ec45` |
| emenda | cf-ec-(n) | `cf-ec-45` |
| título | (obra)-tit-(n) | `cf-1988-tit-2` |
| capítulo | ...-cap-(n) | `cf-1988-tit-2-cap-1` |
| seção | ...-sec-(n) | `cf-1988-tit-2-cap-1-sec-1` |
| artigo (corpo) | (obra)-art-(n) | `cf-1988-art-5` |
| artigo (ADCT) | (obra)-adct-art-(n) | `cf-1988-adct-art-1` |
| caput | ...-caput | `cf-1988-art-5-caput` |
| inciso | ...-inc-(rom) | `cf-1988-art-5-inc-ix` |
| alínea | ...-ali-(letra) | `cf-1988-art-5-inc-ix-ali-a` |
| parágrafo | ...-par-(n) | `cf-1988-art-5-par-1` |
| decisão | (tribunal)-(classe)-(n) | `stf-adi-4650` |
| súmula | (tribunal)-sv-(n) | `stf-sv-11` |
| subject | subject-(tema) | `subject-saude` |
| anotação | anotacao-(ctx) | `anotacao-cf1988-art5-ec45` |
| argumento | arg-(contexto) | `arg-adi4650-financiamento-privado` |
| actor | (papel)-(nome) | `ministro-barroso` |
| actor sistema | sistema-(nome) | `sistema-pipeline` |

> Slug identifica. Path posiciona. Slug nunca muda. UUID é a FK real.

---

# 17. CAMADA 3 — PROVENANCE

```
provenance
  provenance_id    uuid PK DEFAULT gen_random_uuid()
  target_id        uuid NOT NULL
  target_table     text NOT NULL
  source_type      text NOT NULL
  source_url       text
  pipeline_version text
  confidence       float
  hash_input       text
  hash_output      text
  produced_at      timestamptz DEFAULT now()
```

> `target_id` referencia o uuid do primitivo.
> `target_table`: objects, actors, events, edges.
> source_types: manual, scraping, parsing, pipeline, ia.
> Nenhum dado sem provenance. Confidence ordena conflitos.

---

# 18. CAMADA 4 — DERIVADOS

```
chunks
  chunk_slug       text PK
  object_id        uuid NOT NULL
  chunk_text       text NOT NULL
  chunk_index      integer NOT NULL
  token_estimate   integer
  hash_chunk       text

embeddings
  chunk_slug       text FK → chunks
  embedding_model  text NOT NULL
  vector_ref       vector(1536)
  created_at       timestamptz DEFAULT now()
  UNIQUE (chunk_slug, embedding_model)

published_objects
  slug             text PK
  payload_json     jsonb NOT NULL
  payload_hash     text NOT NULL
  updated_at       timestamptz DEFAULT now()
```

> Embedding nunca substitui estrutura. JSON nunca é base primária.

---

# 19. CAMADA 5 — PADRÕES E VIEWS

```sql
v_objects_readable
  id, slug, type_slug, domain_slug, ontological_class, payload, valid_from, valid_to

v_edges_readable
  edge_id, type_slug, epistemic_class,
  source_id, source_slug, target_id, target_slug,
  weight, payload, valid_from, valid_to

v_current_state
  id, slug, type_slug, domain_slug, current_state, last_event_at

v_tree_nodes
  id, slug, type_slug, parent_id, parent_slug, path_slug,
  depth_level, sibling_order, domain_slug

v_decidability_index
  node_id, node_slug, domain_slug, edge_count_by_type, total_edges
```

## 19.2 Views preditivas

```sql
v_decision_signals
  case_id, case_slug, subject_slugs[], class_code, rapporteur_slug,
  outcome, outcome_polarity, decision_direction, uses_modulation,
  reasoning_style, fiscal_effect, decision_unanimity, period

v_actor_decision_profile
  actor_id, actor_slug, total_decisions,
  procedencia_rate, modulacao_rate, contencao_fiscal_rate,
  deference_pattern, dominant_reasoning_style

v_norm_decision_profile
  node_id, node_slug, activation_count, associated_classes[],
  procedencia_rate, expansion_rate, restriction_rate,
  avg_fiscal_effect

v_predictive_features
  case_id, case_slug, subject_vector, normative_targets[],
  class_code, rapporteur_slug, court_composition_hash,
  historical_similarity_score,
  outcome_label, direction_label, modulation_label,
  fiscal_effect_label
```

## 19.3 Fórmulas preditivas

### Probabilidade de resultado
```
P(outcome | subject + article + class + relator + periodo)
```

### Probabilidade de direção
```
P(decision_direction | subject + fundamento + historico_do_orgao)
```

### Probabilidade de modulação
```
P(uses_modulation | impacto_fiscal + tipo_acao + historico)
```

### Índice de Contenção Fiscal (ICF)
```
ICF = decisoes_com_contencao / decisoes_fiscalmente_relevantes
```

### Índice de Expansividade Decisória (IED)
```
IED = decisoes_expansivas / total_decisoes
```

### Índice de Estabilidade Interpretativa (IEI)
```
IEI = confirmacoes / (confirmacoes + superacoes + contradicoes)
```

> Views preditivas são recalculáveis e servem como features para modelos de ML.
> Nenhuma predição é armazenada como fato — predição é derivado.

> Views recalculáveis. Incluem slugs resolvidos e domain denormalizado.

---

# 20. IDENTIDADE MULTINÍVEL

| Nível | Campo | Função |
|---|---|---|
| identidade interna | id (uuid) | consistência, FK |
| identidade pública | slug | leitura, API |
| domínio | type → domain | pertencimento institucional |
| classe ontológica | type → ontological_class | natureza do ente |
| versão | hash_content | estado do dado |
| estado | último event to_state | ciclo de vida |
| tema | edges `sobre` | assunto |
| papel | edges `exerce_papel` | função |
| classe epistêmica | edge_type → epistemic_class | natureza da relação |
| granularidade | chunk_slug | busca semântica |
| posição | path_slug (cache) | árvore |
| origem | provenance_id | de onde veio |

---

# 21. REGRAS DE VÍNCULO

1. Vincular ao nó mais específico
2. Nunca colapsar no caput
3. Subir por agregação
4. Registrar incerteza (confidence no provenance)
5. Separar inferido de confirmado (source_type no provenance)
6. Edges interpretativos devem ter weight (confidence)
7. Distinguir relação epistêmica: não misturar fato com interpretação

---

# 22. OPERAÇÕES SOBRE DADOS

| Operação | Como | Obrigatório |
|---|---|---|
| **Criar** | INSERT primitivo + provenance | provenance |
| **Corrigir** | UPDATE payload + event `correcao` + provenance | event + provenance |
| **Encerrar** | `valid_to` + event `anulacao` | event |
| **Relacionar** | INSERT edge + provenance | provenance |
| **Mudar estado** | event com `to_state` | event |
| **Versionar** | INSERT versão + events nos nós | events |

> Nunca DELETE. Nunca UPDATE sem event. Nunca INSERT sem provenance.

---

# 23. ÍNDICES RECOMENDADOS

```
objects:     (type_slug), (slug), (valid_from), (valid_to)
actors:      (type_slug), (slug), (valid_from)
events:      (aggregate_id, occurred_at), (type_slug), (actor_id)
edges:       (type_slug, source_id), (type_slug, target_id),
             (source_id), (target_id)
edges:       GIN (payload)
events:      GIN (payload)
provenance:  (target_id, target_table)
```

---

# 24. ESCALABILIDADE

* rebuild parcial por domínio
* reindexação por hash
* chunking incremental
* embeddings sob demanda
* expansão por INSERT em domains + types
* política de relevância via weight obrigatório em edges interpretativos

---

# 25. BUSCA

* **Lexical:** filtros por domínio, type, subject, classe ontológica, classe epistêmica, período
* **Semântica:** similaridade via embeddings
* **Híbrida:** filtro + ranking semântico

---

# 26. PIPELINE

1. ingestão (RAW)
2. canonização (slug, type, domain, classes)
3. parsing (extração estruturada)
4. vinculação (edges entre objects)
5. provenance (registro de origem)
6. normalização (texto limpo)
7. atribuição de subjects (edges `sobre`)
8. atribuição de estado inicial (event com `to_state`)
9. extração de argumentos (objects tipo `argumento`, `fundamento`, `tese` + edges `suporta`, `contradiz`, `fundamenta`, `apoia`, `confirma`, `supera`)
10. extração de sinais decisórios (payload de `julgamento` com outcome, direction, modulation, reasoning_style, fiscal_effect)
11. vinculação fiscal (edges `impacta_orcamento`, `aloca_risco_fiscal`, objects `impacto_orcamentario`)
12. chunking (segmentação)
13. embeddings (representação semântica)
14. materialização de views estruturais + preditivas
15. publicação (published_objects)

---

# 27. ERROS PROIBIDOS

* colapsar estrutura
* modelar por tela
* usar slug como única estrutura
* misturar camadas
* embeddar antes de estruturar
* perder vínculo com fonte
* **hardcodar domínios**
* **zona de integração como camada fixa**
* **dado sem provenance**
* **tabela para o que cabe nos 4 primitivos**
* **estado como campo — estado é derivado**
* **tema como campo — tema é edge**
* **slug duplicado entre tabelas**
* **payload como fonte de verdade para relações**
* **DELETE — encerrar com valid_to**
* **event sem actor**
* **relação como campo — relação é edge**
* **duplicar árvore para versionar**
* **usar slug como FK relacional — UUID é a FK**
* **misturar classes epistêmicas — fato ≠ interpretação ≠ classificação**
* **edge interpretativo sem weight — confidence obrigatório**
* **julgamento sem sinal decisório — outcome e direction são obrigatórios**
* **predição armazenada como fato — predição é sempre derivado**
* **fundamento sem vínculo a norma ou decisão — fundamento solto é ruído**

---

# 28. FÓRMULA DE EXPANSÃO

```text
1. INSERT em domains
2. INSERT em *_types com domain_slug + classe
3. INSERT em state_types
4. INSERT em objects · actors · events · edges (com uuid)
5. INSERT em provenance (com target_id uuid)
6. Materializar views
7. Derivados se recalculam

Nunca ALTER TABLE. Nunca redesenho. Nunca partir do zero.
```

---

# 29. FÓRMULA FINAL

```text
DOMAINS (N, hierárquicos, inclui transversal)
→ TAXONOMIAS (
    object_types + ontological_class
    actor_types + actor_class
    event_types + event_class
    edge_types + epistemic_class
    state_types
  )
→ PRIMITIVOS (
    objects [id uuid + slug]
    actors [id uuid + slug]
    events [aggregate_id + actor_id uuid]
    edges [source_id + target_id uuid]
  )
→ PROVENANCE (target_id uuid)
→ VIEWS MATERIALIZADAS (estruturais + preditivas)
→ DERIVADOS (chunks · embeddings · JSON)
→ API / VIEWS
```

---

# 30. PRINCÍPIO FINAL

> O sistema não organiza textos.
> Ele organiza relações estruturadas entre textos, decisões, normas, instituições, argumentos e sinais decisórios, em múltiplos domínios, escalas e classes epistêmicas.
> O átomo de hoje é a cartografia do contencioso constitucional.
> O cosmos de amanhã é INSERT.
> A cartografia não apenas mapeia o passado — ela projeta o futuro.

---

**Este protocolo define a arquitetura permanente do sistema.
Nenhuma implementação deve violar suas regras estruturais.**

**v8 — 25 de março de 2026**
**Damares Medina**
