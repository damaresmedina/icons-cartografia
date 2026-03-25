# PROTOCOLO ONTOLÓGICO UNIVERSAL v9

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
25. **O sistema é autoensinável apenas na camada de perfis** — o aprendizado incide sobre regularidades observadas em decisões por relator e órgão, sem autoalteração do núcleo ontológico
26. **Toda aprendizagem é mediada por membrana** — recorrência empírica vira hipótese, hipótese vira estrutura apenas após validação
27. **Perfis decisórios são derivados** — dinâmicos e revisáveis, nunca fonte primária de verdade
28. **Ambiente de julgamento é variável estruturante** — deve ser capturado no evento e correlacionado com órgão, relator, tema e técnica decisória

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
| ente_orcamentario | transversal | estrutural | Ente ou centro de impacto orçamentário |
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
| impacta_orcamento | juridico | transversal | fiscal | true | magnitude (0-1) | true | decisão impacta orçamento de ente |
| aloca_risco_fiscal | juridico | transversal | fiscal | true | magnitude (0-1) | true | decisão redistribui risco fiscal |
| quantifica | transversal | transversal | fiscal | true | confidence (0-1) | false | vincula estimativa a impacto |
| mitiga_impacto | juridico | juridico | fiscal | true | eficacia (0-1) | false | modulação mitiga impacto fiscal |
| externaliza_risco | juridico | transversal | fiscal | true | magnitude (0-1) | false | decisão transfere risco a terceiro |
| decide_em_favor_de | juridico | transversal | preditiva | true | confidence (0-1) | false | decisão favorece parte/ente |
| gera_impacto_orcamentario | juridico | transversal | fiscal | true | magnitude (0-1) | false | decisão gera impacto orçamentário |
| fundamenta | juridico | juridico | argumentativa | true | forca (0-1) | false | fundamento embasa decisão |
| apoia | juridico | juridico | argumentativa | true | forca (0-1) | false | fundamento/tese apoia outro |
| confirma | juridico | juridico | argumentativa | true | confidence (0-1) | false | decisão confirma precedente |
| supera | juridico | juridico | argumentativa | true | confidence (0-1) | false | decisão supera precedente |
| modula | juridico | juridico | fiscal | true | eficacia (0-1) | false | decisão modula efeitos |

> `weight_semantics` declara o que o weight significa para cada tipo.
> `weight_required` indica se o weight é obrigatório na inserção.

### Regra de target fiscal

> Edges fiscais semanticamente completos não devem apontar para target NULL. O alvo deve ser um object ou actor que represente o ente, fundo, regime ou centro de impacto afetado (ex: `ente-uniao`, `ente-estado-sp`, `fundo-fgts`, `regime-rpps`).

### Entes orçamentários

> Entes afetados por impacto fiscal são objects do type `ente_orcamentario` (domain: transversal, ontological_class: estrutural), com slugs próprios: `ente-uniao`, `ente-estado-sp`, `ente-municipio-rj`, `fundo-fgts`, `regime-rpps`.

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
> `aggregate_id` aponta para objects.id ou actors.id. Slugs são resolvidos apenas em views legíveis.

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

## 8.7 Camada de ambiente de julgamento

Payload obrigatório em todo julgamento colegiado:

```json
{
  "decision_body": "plenario | primeira_turma | segunda_turma | secao | orgao_especial",
  "collegiality_mode": "colegiado | monocratico",
  "adjudication_environment": "virtual | presencial | hibrido",
  "session_format": "sincrona | assincrona | mista",
  "oral_argument_present": true,
  "public_debate_intensity": "alta | media | baixa | inexistente"
}
```

Campos derivados recomendados:

```json
{
  "panel_size": 11,
  "votes_present": 10,
  "agu_manifested": true,
  "pgr_manifested": false,
  "amicus_participation": true
}
```

> Ambiente de julgamento não é detalhe procedimental — é variável decisória.
> O filtro de ambiente só é computado como variável colegiada quando `collegiality_mode = colegiado`.
> Todas as views analíticas e preditivas devem permitir filtragem por ambiente de julgamento.

### Regra de canonicalização do ambiente

> Toda análise de ambiente de julgamento deve derivar de um mapeamento canônico único baseado no event_type = julgamento. Campos canônicos: `decision_body`, `collegiality_mode`, `adjudication_environment`, `session_format`, `oral_argument_present`, `public_debate_intensity`. Nenhuma view analítica pode redefinir localmente o significado desses campos. Toda view deve herdá-los da camada canônica de julgamento.

## 8.8 Regras

> Todo julgamento deve conter no mínimo: `outcome`, `decision_direction`, `uses_modulation`, `reasoning_style`, `fiscal_effect`, `decision_body`, `adjudication_environment`.
> Fundamentos e teses são objects com existência própria — podem ser referenciados por múltiplas decisões.
> A camada prospectiva não altera primitivos — apenas enriquece types, payloads, edges e views.

## 8.9 Rastreabilidade dos sinais prospectivos

> Todo campo prospectivo ou interpretativo deve declarar no payload:
> * `extraction_method`: manual | automatico | hibrido
> * `confidence_score`: float (0-1)

Campos sujeitos a esta regra:
* `decision_direction`, `rights_effect`, `state_constraint`
* `uses_modulation`, `temporal_effect`, `injunctive_profile`
* `deference_level`, `reasoning_style`
* `fiscal_effect`, `fiscal_risk_shift`, `retroactive_liability`

> Quando o payload do event contiver campos prospectivos ou analíticos, deve incluir `extraction_method` e `confidence_score`. Provenance deve registrar `source_type`, `pipeline_version`, `hash_input`, `confidence` e método de extração.

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

# 10. SISTEMA AUTOENSINÁVEL

## 10.1 Princípio

> O sistema é autoensinável apenas na camada de perfis, padrões e features derivadas. O aprendizado incide sobre regularidades observadas em decisões por relator e órgão decisório, sem autoalteração do núcleo ontológico.

> Toda aprendizagem decisória é mediada por uma membrana de consistência, que converte recorrência empírica em hipótese analítica, e hipótese analítica em estrutura reconhecida apenas após validação.

> O banco aprende; a ontologia decide o que pode virar conhecimento estrutural.

## 10.2 Objeto de aprendizado

O sistema aprende progressivamente:

**Por relator:**
* taxa de procedência / improcedência
* frequência de não conhecimento
* propensão à modulação
* intensidade de contenção fiscal
* direção decisória recorrente
* estilo argumentativo dominante
* frequência de deferência institucional
* perfil por classe processual, tema e dispositivo
* variação por ambiente de julgamento (virtual vs presencial)

**Por órgão:**
* distribuição de resultados
* temas sensíveis
* rigidez ou expansividade média
* técnica decisória típica
* grau de estabilidade
* variação por ambiente de julgamento

**Por relator + órgão:**
* o relator muda quando sai do monocrático para colegiado?
* o órgão contém ou amplifica o padrão individual?
* quais relatores convergem mais com certo órgão?
* quais órgãos produzem mais variação interna?

## 10.3 Arquitetura do autoensino

```text
DECISÕES NOVAS
→ extração estruturada de sinais
→ agregação por relator
→ agregação por órgão
→ detecção de regularidades
→ geração de hipótese decisória
→ MEMBRANA ONTOLÓGICA
→ incorporação controlada
→ refinamento dos perfis
```

## 10.4 Core fixo vs camada autoensinável

| Camada | O que contém | Pode mudar? |
|---|---|---|
| **Core fixo** | 4 primitivos, identidade dual, classes ontológicas, integridade relacional, temporalidade, provenance | NÃO |
| **Autoensinável** | perfis decisórios, clusters por relator, estilos, padrões de órgão, correlações, features preditivas | SIM (por INSERT) |

## 10.5 Perfis derivados

```
learned_decision_profiles
  profile_id            uuid PK DEFAULT gen_random_uuid()
  profile_type          text NOT NULL
  target_slug           text NOT NULL
  period_start          date
  period_end            date
  sample_size           integer
  profile_payload       jsonb
  confidence_score      float
  stability_score       float
  predictive_gain       float
  status                text DEFAULT 'proposed'
  created_at            timestamptz DEFAULT now()
```

Valores de `profile_type`:
* `relator` — perfil de ministro/relator
* `orgao` — perfil de órgão decisório
* `relator_orgao` — perfil cruzado relator × órgão
* `relator_environment` — perfil do relator por ambiente
* `orgao_environment` — perfil do órgão por ambiente

Valores de `status`:
* `proposed` — hipótese gerada pelo sistema
* `validated` — aprovada pela membrana
* `incorporated` — integrada às features preditivas
* `rejected` — descartada
* `superseded` — substituída por perfil mais recente

## 10.6 Propostas ontológicas

```
ontology_proposals
  proposal_id           uuid PK DEFAULT gen_random_uuid()
  proposal_type         text NOT NULL
  description           text
  evidence_payload      jsonb
  recurrence_count      integer
  stability_score       float
  predictive_gain       float
  compatibility_score   float
  status                text DEFAULT 'pending'
  created_at            timestamptz DEFAULT now()
  reviewed_at           timestamptz
```

Valores de `proposal_type`:
* `new_decision_pattern` — padrão decisório novo
* `new_reasoning_pattern` — padrão argumentativo novo
* `new_fiscal_pattern` — padrão fiscal novo
* `new_predictive_feature` — feature preditiva candidata
* `new_body_pattern` — padrão de órgão novo
* `new_relator_pattern` — padrão de relator novo
* `new_environment_pattern` — padrão sensível ao ambiente

## 10.7 A membrana

Opera em 3 níveis:

**Nível 1 — Observação livre**
O sistema observa tudo: frequências, desvios, clusters, correlações, anomalias.

**Nível 2 — Proposta controlada**
O sistema sugere: novo padrão, nova tipologia, nova feature, refinamento de perfil. Apenas como proposta.

**Nível 3 — Incorporação condicionada**
Só entra no modelo oficial se passar por:
* recorrência mínima (recurrence_count)
* estabilidade temporal (stability_score)
* ganho discriminatório (predictive_gain)
* compatibilidade com a ontologia (compatibility_score)
* utilidade preditiva demonstrada

## 10.8 Fluxo de autoensino

1. **Ingestão** — entra nova decisão
2. **Extração** — pipeline extrai: relator, órgão, ambiente, outcome, direção, modulação, fundamento, efeito fiscal
3. **Atualização** — recalcula perfis derivados
4. **Detecção** — compara perfil anterior vs atual, identifica tendência de deslocamento
5. **Hipótese** — gera hipótese analítica (ex: "Relator X apresenta aumento de modulação em virtual nos últimos 18 meses")
6. **Membrana** — hipótese recebe scores de confiança, estabilidade e ganho preditivo
7. **Incorporação** — se aprovada: vira feature oficial, vira padrão reconhecido

## 10.9 Regras

> Perfis decisórios são derivados, dinâmicos e revisáveis; nunca fonte primária de verdade.
> O sistema não altera automaticamente o núcleo ontológico.
> Toda incorporação passa pela membrana de 3 níveis.
> Perfis sensíveis ao ambiente devem carregar `environment_sensitive: true` e `environment_effect_strength`.

---

# 11. VIDA PROCESSUAL, AMBIENTE DECISÓRIO E ECOLOGIA INSTITUCIONAL

## 11.1 Princípio Geral

> Cada unidade processual é modelada como uma entidade persistente no tempo, dotada de ciclo de vida próprio. Seus eventos não são atributos periféricos, mas os acontecimentos constitutivos de sua trajetória institucional.

## 11.2 Princípio da Vida Processual

> O processo não é uma fotografia. É uma linha de vida institucional. O estado é apenas a expressão derivada de seu acontecimento mais recente.

## 11.3 Princípio do Acontecimento Qualificado

> Todo acontecimento processual juridicamente relevante deve registrar não apenas que ocorreu, mas quando ocorreu, em que ambiente ocorreu, em que órgão ocorreu e sob que configuração institucional ocorreu.

## 11.4 Princípio da Ecologia Decisória

> Nenhum julgamento colegiado deve ser modelado apenas por relator e órgão. Sua representação ontológica deve incluir, sempre que disponíveis, os demais atores relevantes, seus papéis contextuais e suas correlações com ambiente, tempo, tema e resultado.

## 11.5 Contrato mínimo da ecologia decisória

Todo julgamento colegiado deve registrar **obrigatoriamente**:
* 1 relator
* 1 órgão decisório
* 1 ambiente de julgamento
* panel_size
* votes_present

Sempre que disponível, devem ser registrados:
* presidente da sessão
* divergência
* pedido de vista
* destaque
* manifestação da AGU
* manifestação da PGR/MP
* participação de amicus
* sustentação oral

> Regra de completude mínima: nenhuma linha de `v_judgment_ecology` é válida sem relator, órgão, ambiente, panel_size e votes_present.

> Regra de completude da ecologia decisória: todo julgamento colegiado deve conter obrigatoriamente relator, órgão decisório, ambiente de julgamento, panel_size e votes_present. Eventos de julgamento que não atendam a esses requisitos são considerados incompletos e não devem ser utilizados em análises agregadas ou preditivas.

## 11.6 Princípio do Ambiente

> O ambiente de julgamento integra a temporalidade do processo. Ele influencia a forma, a intensidade e o resultado dos acontecimentos decisórios ao longo de sua vida institucional.

## 11.6 Regra Estrutural

> Tempo e ambiente são dimensões constitutivas do evento. Não são contexto externo nem detalhe de interface.

## 11.7 Unidade Central

| Conceito | Definição |
|---|---|
| processo | entidade persistente |
| evento | acontecimento |
| estado | síntese derivada |
| trajetória | sequência ordenada de acontecimentos |
| ambiente | condição institucional do acontecimento |
| ecologia decisória | correlação entre atores, órgão, tema, tempo e ambiente |

## 11.8 Atores Relevantes

A ecologia decisória deve admitir, sempre que houver dado disponível:

**Atores jurisdicionais:**
* relator, presidente da sessão, revisor
* votantes, divergentes
* autor de pedido de vista, autor de destaque
* ausentes

**Atores processuais e institucionais:**
* requerente / recorrente / impetrante
* requerido / recorrido / impetrado
* AGU, PGR / MP, defensorias
* amici curiae, partidos, entidades de classe
* entes federativos, advocacias públicas

## 11.9 Regra dos Papéis

> Payload resume; edges explicam.

Papéis contextuais modelados por `exerce_papel`:

```
ministro-barroso --[exerce_papel]--> julgamento-x
  payload: { "role": "relator" }

ministro-fachin --[exerce_papel]--> julgamento-x
  payload: { "role": "divergente" }

agu --[exerce_papel]--> julgamento-x
  payload: { "role": "manifestante" }

pgr --[exerce_papel]--> julgamento-x
  payload: { "role": "custos_legis_manifestante" }

amicus-abcd --[exerce_papel]--> julgamento-x
  payload: { "role": "amicus_curiae" }
```

## 11.10 Temporalidade da Vida Processual

| Plano | Campo | Significado |
|---|---|---|
| tempo do acontecimento | `occurred_at` | quando o evento ocorreu |
| tempo da validade | `valid_from` / `valid_to` | vigência |
| tempo do registro | `recorded_at` | quando o sistema soube |
| tempo da trajetória | sequência de events | vida processual |

> O estado processual é sempre derivado da sequência temporal dos acontecimentos, e nunca substitui a história do processo.

## 11.11 Filtros Estruturais Obrigatórios

As views e consultas devem permitir filtragem por:

* relator, órgão decisório, colegialidade
* ambiente (virtual, presencial, híbrido)
* tema, classe processual
* demais atores relevantes
* período, resultado, direção
* técnica decisória, efeito fiscal/material

## 11.12 Correlações Obrigatórias

A camada analítica deve permitir, no mínimo:

| Eixo A | × | Eixo B |
|---|---|---|
| tempo | × | ambiente |
| relator | × | ambiente |
| órgão | × | ambiente |
| relator | × | órgão |
| relator | × | outros ministros |
| tema | × | ambiente |
| tema | × | atores |
| classe processual | × | ambiente |
| classe processual | × | atores |
| resultado | × | ambiente |
| direção | × | ambiente |
| modulação/técnica | × | ambiente |
| efeito fiscal | × | atores |
| efeito fiscal | × | ambiente |

## 11.13 Views de Vida Processual

```sql
v_process_lifecycle
  processo_id, processo_slug, data_nascimento, evento_mais_recente,
  estado_atual, duracao_total, numero_eventos, sequencia_marcos[]

v_process_trajectory_patterns
  pattern_type, sequencia[], frequencia, duracao_media

v_judgment_ecology
  caso_id, caso_slug, relator_slug, orgao, ambiente, tempo,
  temas[], atores_participantes[], papeis[],
  outcome, direction, tecnica, efeito_fiscal

v_collegial_dynamics
  julgamento_id, composicao[], vista_presente, destaque_presente,
  divergencia_presente, migracao_ambiente
```

## 11.14 Fórmulas de Vida Processual

### Duração da Vida Processual
```
DVP = último_evento - distribuição
```

### Tempo Entre Marcos
```
TEM = evento_n - evento_(n-1)
```

### Índice de Interrupção Processual
```
IIP = eventos_suspensivos / total_eventos
```

### Índice de Complexidade da Trajetória
```
ICT = eventos_distintos × duração × bifurcações
```

### Taxa de Conversão Virtual → Presencial
```
TCVP = julgamentos_com_destaque / julgamentos_virtuais
```

### Tempo de Migração Entre Ambientes
```
TM = julgamento_presencial - julgamento_virtual
```

### Índice de Virtualização por Relator
```
IVR = julgamentos_virtuais / total_julgamentos
```

## 11.15 Regra de Não-Colonização

> O corpus pode ensinar a ontologia a enxergar melhor padrões decisórios. Ele não pode redefinir sozinho a estrutura do sistema.

## 11.16 Objetivo Prospectivo

> A ontologia deve estar preparada não apenas para reconstruir a trajetória dos processos, mas para projetar padrões futuros de percurso, ambiente, comportamento decisório e interação institucional.

## 11.17 Princípio Final da Camada

> O acontecimento decisório é uma ecologia institucional temporalmente situada, e não uma relação binária entre processo e resultado.

---

# 12. VERSIONAMENTO

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

# 13. EQUIVALÊNCIA v1 → v9

| v1 | v9 | Como |
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

# 14. ÁRVORE UNIVERSAL

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

# 15. SUBJECTS (TEMAS)

Objects type `subject` (transversal, ontological_class: semantico). Hierarquia via `parent_of`. Vinculação via edge `sobre`.

```
subject-saude --[parent_of]--> subject-saude-publica
stf-adi-4650 --[sobre]--> subject-financiamento-eleitoral
cf-1988-art-196 --[sobre]--> subject-saude
```

---

# 16. ANOTAÇÕES

Objects type `anotacao` (transversal, ontological_class: editorial). Edge `annota` ao nó mais específico.

---

# 17. PAPÉIS (ROLES)

Edge `exerce_papel` (epistemic_class: institucional) com `{role: "relator"}` no payload.

## Papéis mínimos obrigatórios no julgamento colegiado

| Role | Obrigatoriedade |
|---|---|
| `relator` | obrigatório |
| `orgao_decisorio` | obrigatório |
| `votante` | recomendável |
| `presidente_sessao` | recomendável |
| `divergente` | quando houver |
| `autor_vista` | quando houver |
| `autor_destaque` | quando houver |
| `manifestante_agu` | quando houver |
| `manifestante_pgr` | quando houver |
| `amicus_curiae` | quando houver |

---

# 18. CONVENÇÃO DE SLUG

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

# 19. CAMADA 3 — PROVENANCE

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

# 20. CAMADA 4 — DERIVADOS

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

# 21. CAMADA 5 — PADRÕES E VIEWS

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

## 19.2 View canônica de ambiente

```sql
v_judgment_environment_canonical
  event_id, aggregate_id, decision_body, collegiality_mode,
  adjudication_environment, session_format,
  oral_argument_present, public_debate_intensity,
  panel_size, votes_present
```

> Regra: todas as views analíticas que utilizem ambiente de julgamento devem resolver esse eixo a partir de `v_judgment_environment_canonical`.

## 19.3 Views preditivas

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

## 19.4 Fórmulas preditivas

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

## 20.4 Views de ambiente e perfil decisório

```sql
v_judgment_environment_profile
  case_id, case_slug, relator_slug, decision_body,
  adjudication_environment, session_format, outcome,
  decision_direction, uses_modulation, fiscal_effect, subjects[]

v_relator_decision_profile
  actor_id, actor_slug, total_decisions,
  procedencia_rate, modulacao_rate, contencao_fiscal_rate,
  deference_pattern, dominant_reasoning_style

v_relator_environment_profile
  actor_id, actor_slug, environment,
  total_decisions, outcome_rate_by_env,
  modulation_rate_by_env, fiscal_containment_by_env

v_body_decision_profile
  decision_body, total_decisions, outcome_distribution,
  direction_distribution, modulation_rate, avg_fiscal_effect

v_body_environment_profile
  decision_body, environment, total_decisions,
  outcome_distribution, subjects_by_env[]

v_relator_orgao_decision_profile
  actor_slug, decision_body, total_decisions,
  procedencia_rate, convergence_with_body,
  divergence_rate, modulation_rate

v_subject_environment_profile
  subject_slug, environment, total_decisions,
  dominant_relator, dominant_body,
  direction_profile_by_env

v_actor_environment_interactions
  actor_slug, actor_type, environment,
  participation_rate, correlation_with_outcome,
  correlation_with_modulation

v_emerging_decision_patterns
  pattern_id, pattern_type, description,
  recurrence, stability, predictive_gain, status
```

> Views recalculáveis. Incluem slugs resolvidos e domain denormalizado.

---

# 22. IDENTIDADE MULTINÍVEL

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

# 23. REGRAS DE VÍNCULO

1. Vincular ao nó mais específico
2. Nunca colapsar no caput
3. Subir por agregação
4. Registrar incerteza (confidence no provenance)
5. Separar inferido de confirmado (source_type no provenance)
6. Edges interpretativos devem ter weight (confidence)
7. Distinguir relação epistêmica: não misturar fato com interpretação

---

# 24. OPERAÇÕES SOBRE DADOS

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

# 25. ÍNDICES RECOMENDADOS

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

# 26. ESCALABILIDADE

* rebuild parcial por domínio
* reindexação por hash
* chunking incremental
* embeddings sob demanda
* expansão por INSERT em domains + types
* política de relevância via weight obrigatório em edges interpretativos

---

# 27. BUSCA

* **Lexical:** filtros por domínio, type, subject, classe ontológica, classe epistêmica, período
* **Semântica:** similaridade via embeddings
* **Híbrida:** filtro + ranking semântico

---

# 28. PIPELINE

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
14. materialização de views estruturais + preditivas + ambiente
15. atualização de perfis decisórios (learned_decision_profiles)
16. detecção de padrões emergentes (ontology_proposals)
17. publicação (published_objects)

---

# 29. ERROS PROIBIDOS

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
* **perfil decisório tratado como fato — perfis são derivados, revisáveis**
* **autoalteração do core ontológico — só a camada de perfis aprende**
* **incorporação sem membrana — toda hipótese passa por validação de 3 níveis**
* **julgamento colegiado sem ambiente — adjudication_environment obrigatório**

---

# 30. FÓRMULA DE EXPANSÃO

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

# 31. FÓRMULA FINAL

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
→ VIEWS MATERIALIZADAS (estruturais + preditivas + ambiente + perfis)
→ PERFIS APRENDIDOS (learned_decision_profiles)
→ MEMBRANA (ontology_proposals)
→ DERIVADOS (chunks · embeddings · JSON)
→ API / VIEWS
```

---

# 32. PRINCÍPIO FINAL

> O sistema não organiza textos.
> Ele organiza relações estruturadas entre textos, decisões, normas, instituições, argumentos e sinais decisórios, em múltiplos domínios, escalas e classes epistêmicas.
> O átomo de hoje é a cartografia do contencioso constitucional.
> O cosmos de amanhã é INSERT.
> A cartografia não apenas mapeia o passado — ela projeta o futuro.
> O banco aprende; a ontologia decide o que pode virar conhecimento estrutural.

---

**Este protocolo define a arquitetura permanente do sistema.
Nenhuma implementação deve violar suas regras estruturais.**

**v9 — 25 de março de 2026**
**Damares Medina**
