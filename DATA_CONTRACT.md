# DATA CONTRACT — DICIONÁRIO DE CAMPOS

## Cartografia do Litigioso Brasileiro

**Derivado de:** CONSTITUICAO_ONTOLOGICA.md
**Finalidade:** Definir para cada type crítico o que é obrigatório, opcional, inferível e proibido no payload
**Uso:** O pipeline lê este contrato antes de inserir qualquer dado

---

## Legenda

| Símbolo | Significado |
|---|---|
| **OBR** | obrigatório — pipeline rejeita sem este campo |
| **REC** | recomendado — pipeline aceita sem, mas emite warning |
| **OPC** | opcional — presente apenas quando disponível |
| **INF** | inferível — pode ser derivado automaticamente de outros campos ou edges |
| **PRO** | proibido — não deve existir no payload (pertence a outra camada) |
| **EXT** | extraction_method + confidence_score obrigatórios quando presente (campo prospectivo) |

---

# 1. OBJECTS

## 1.1 `constituicao`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `title` | OBR | text | Nome da constituição |
| `jurisdiction` | OBR | text | Jurisdição (ex: "BR") |
| `promulgation_date` | OBR | date | Data de promulgação |
| `source_url` | REC | text | URL da fonte original |
| `total_articles` | OPC | int | Quantidade total de artigos |
| `total_amendments` | INF | int | Derivável da contagem de edges `amends` |

## 1.2 `titulo`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Denominação do título |
| `sibling_order` | OBR | int | Ordem entre irmãos |
| `numero_romano` | OBR | text | Numeral romano (ex: "II") |
| `numero_int` | REC | int | Numeral inteiro (ex: 2) |
| `path_slug` | INF | text | Derivado dos edges `parent_of` |
| `depth_level` | INF | int | Derivado |
| `is_leaf` | INF | bool | Derivado |

## 1.3 `capitulo`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Denominação do capítulo |
| `sibling_order` | OBR | int | Ordem entre irmãos |
| `numero_romano` | OBR | text | Numeral romano |
| `numero_int` | REC | int | Numeral inteiro |
| `path_slug` | INF | text | Derivado |
| `depth_level` | INF | int | Derivado |

## 1.4 `secao`

Ontological class: estrutural · Domain: normativo

Mesmo padrão de `capitulo`.

## 1.5 `artigo`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Texto do caput ou referência |
| `sibling_order` | OBR | int | Ordem (número do artigo) |
| `numero_texto` | REC | text | Texto do número (ex: "5º") |
| `adct` | REC | bool | true se pertence ao ADCT |
| `path_slug` | INF | text | Derivado |
| `depth_level` | INF | int | Derivado |
| `is_leaf` | INF | bool | Derivado |
| `is_repealed` | INF | bool | Derivado do último event de estado |
| `normalized_text` | INF | text | Derivado de text_content |

## 1.6 `caput`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Texto do caput |
| `normalized_text` | INF | text | Derivado |

## 1.7 `inciso`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Texto do inciso |
| `sibling_order` | OBR | int | Ordem numérica |
| `numero_romano` | REC | text | Numeral romano (ex: "IX") |
| `normalized_text` | INF | text | Derivado |

## 1.8 `paragrafo`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Texto do parágrafo |
| `sibling_order` | OBR | int | Número do parágrafo |
| `tipo` | REC | text | "unico" ou "numerado" |
| `numero_texto` | REC | text | Ex: "§ 1º", "Parágrafo único" |
| `normalized_text` | INF | text | Derivado |

## 1.9 `alinea`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Texto da alínea |
| `sibling_order` | OBR | int | Ordem |
| `letra` | REC | text | Letra da alínea (ex: "a") |
| `normalized_text` | INF | text | Derivado |

## 1.10 `acao_direta`

Ontological class: processual · Domain: juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `process_number` | OBR | text | Número do processo (ex: "ADI 4650") |
| `court` | OBR | text | Tribunal (ex: "STF") |
| `class_code` | OBR | text | Classe processual (ex: "ADI") |
| `rapporteur` | REC | text | Slug do relator |
| `judgment_date` | REC | date | Data do julgamento |
| `filing_date` | OPC | date | Data de protocolo |
| `summary_text` | OPC | text | Ementa |
| `full_text` | OPC | text | Inteiro teor |
| `source_url` | REC | text | URL no STF |
| `hash_content` | INF | text | Hash do conteúdo |
| `is_repealed` | PRO | — | Estado é derivado de events |
| `current_state` | PRO | — | Estado é derivado de events |

## 1.11 `recurso_extraordinario`

Mesmo padrão de `acao_direta` com adição de:

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `tema_rg` | REC | int | Número do tema de repercussão geral |
| `leading_case` | REC | bool | Se é o leading case do tema |

## 1.12 `sumula_vinculante`

Ontological class: estrutural · Domain: juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `numero` | OBR | int | Número da súmula |
| `enunciado` | OBR | text | Texto do enunciado |
| `data_aprovacao` | REC | date | Data de aprovação |
| `situacao` | REC | text | "vigente", "cancelada", "revisada" |
| `source_url` | OPC | text | URL |

## 1.13 `emenda_constitucional`

Ontological class: estrutural · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `numero` | OBR | int | Número da emenda |
| `data` | OBR | date | Data de promulgação |
| `ementa` | OBR | text | Ementa da emenda |
| `artigos_alterados` | REC | text[] | Slugs dos artigos alterados |
| `source_url` | OPC | text | URL |

## 1.14 `subject`

Ontological class: semantico · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `label` | OBR | text | Nome do tema |
| `area` | REC | text | Área jurídica (ex: "direito_fundamental") |
| `description` | OPC | text | Descrição do tema |

## 1.15 `anotacao`

Ontological class: editorial · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text` | OBR | text | Texto da anotação |
| `annotation_type` | OBR | text | Tipo: "alteracao", "observacao", "referencia" |
| `author` | REC | text | Autor da anotação |

## 1.16 `argumento`

Ontological class: argumentativo · Domain: juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Texto do argumento/fundamento |
| `argument_type` | OBR | text | "razao_decidir", "obiter_dictum", "voto_divergente", "tese_fixada" |
| `direction` | REC+EXT | text | "procedente", "improcedente", "parcial" |
| `ministro_slug` | REC | text | Slug do ministro que proferiu |
| `extraction_method` | OBR quando `direction` presente | text | "manual", "automatico", "hibrido" |
| `confidence_score` | OBR quando `direction` presente | float | 0.0 a 1.0 |

## 1.17 `fundamento`

Ontological class: argumentativo · Domain: juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Texto do fundamento |
| `fundamento_type` | OBR | text | "constitucional", "legal", "jurisprudencial", "doutrinario" |
| `extraction_method` | REC | text | Como foi extraído |
| `confidence_score` | REC | float | Confiança na extração |

## 1.18 `tese`

Ontological class: argumentativo · Domain: juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `text_content` | OBR | text | Texto da tese |
| `binding` | OBR | bool | Se é vinculante |
| `fixation_date` | OBR | date | Data de fixação |
| `status` | OBR | text | "vigente", "superada", "revisada" |
| `tema_rg` | REC | int | Tema de repercussão geral |

## 1.19 `resultado_decisorio`

Ontological class: preditivo · Domain: juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `outcome` | OBR | text | "procedente", "improcedente", "parcial", "nao_conhecido", "prejudicado" |
| `outcome_polarity` | OBR | text | "favor_autor", "favor_reu", "favor_estado", "favor_particular", "misto" |
| `decision_unanimity` | OBR | text | "unanime", "maioria", "monocratica" |
| `merits_reached` | OBR | bool | Se o mérito foi alcançado |
| `extraction_method` | OBR | text | "manual", "automatico", "hibrido" |
| `confidence_score` | OBR | float | 0.0 a 1.0 |

## 1.20 `impacto_orcamentario`

Ontological class: analitico · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `decisao_slug` | OBR | text | Slug da decisão vinculada |
| `ente_afetado` | OBR | text | Slug do ente orçamentário afetado |
| `direcao` | OBR | text | "aumento_despesa", "reducao_receita", "neutro" |
| `horizonte_temporal` | OBR | text | "imediato", "curto", "medio", "longo" |
| `estimativa_brl` | REC | numeric | Valor estimado em BRL |
| `retroatividade` | REC | bool | Se há efeito retroativo |
| `multiplas_estimativas` | OPC | jsonb[] | Array de estimativas de diferentes fontes |
| `divergencia_metodologica` | OPC | bool | Se há divergência entre estimativas |
| `base_documental` | REC | text | Referência à nota técnica |
| `extraction_method` | OBR | text | "manual", "automatico", "hibrido" |
| `confidence_score` | OBR | float | 0.0 a 1.0 |

## 1.21 `estimativa_fiscal`

Ontological class: analitico · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `valor_brl` | OBR | numeric | Valor em BRL |
| `metodologia` | OBR | text | Metodologia de cálculo |
| `fonte` | OBR | text | Instituição que produziu (ex: "STN", "IFI") |
| `data_referencia` | OBR | date | Data de referência da estimativa |
| `confianca` | OBR | float | Grau de confiança da estimativa |

## 1.22 `ente_orcamentario`

Ontological class: estrutural · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `label` | OBR | text | Nome do ente |
| `ente_type` | OBR | text | "uniao", "estado", "municipio", "fundo", "regime", "orgao" |
| `uf` | OPC | text | UF quando aplicável |
| `cnpj` | OPC | text | CNPJ quando aplicável |

---

# 2. EVENTS

## 2.1 `julgamento`

Event class: juridico · Domain: juridico

### Payload obrigatório (sinais decisórios + ambiente)

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `outcome` | OBR | text | "procedente", "improcedente", "parcial", "nao_conhecido", "prejudicado" |
| `decision_direction` | OBR+EXT | text | "expansiva", "restritiva", "conservadora", "inovadora", "neutra" |
| `uses_modulation` | OBR+EXT | bool | Se houve modulação |
| `reasoning_style` | OBR+EXT | text | "formalista", "consequencialista", "principialista", "pragmatica", "mista" |
| `fiscal_effect` | OBR+EXT | text | "expansivo", "contencao", "neutro", "indeterminado" |
| `decision_body` | OBR | text | "plenario", "primeira_turma", "segunda_turma", "secao", "orgao_especial" |
| `adjudication_environment` | OBR | text | "virtual", "presencial", "hibrido" |
| `collegiality_mode` | OBR | text | "colegiado", "monocratico" |
| `session_format` | REC | text | "sincrona", "assincrona", "mista" |
| `oral_argument_present` | REC | bool | Se houve sustentação oral |
| `public_debate_intensity` | REC | text | "alta", "media", "baixa", "inexistente" |
| `outcome_polarity` | REC | text | "favor_autor", "favor_reu", "favor_estado", "favor_particular", "misto" |
| `decision_unanimity` | REC | text | "unanime", "maioria" |
| `merits_reached` | REC | bool | Se o mérito foi alcançado |
| `rights_effect` | OPC+EXT | text | "amplia", "restringe", "preserva", "indeterminado" |
| `state_constraint` | OPC+EXT | text | "aumenta", "reduz", "mantem" |
| `temporal_effect` | OPC+EXT | text | "ex_tunc", "ex_nunc", "prospectivo", "misto" |
| `injunctive_profile` | OPC+EXT | text | "forte", "medio", "fraco", "inexistente" |
| `deference_level` | OPC+EXT | text | "alto", "medio", "baixo" |
| `fiscal_risk_shift` | OPC+EXT | text | "estado", "particular", "compartilhado" |
| `retroactive_liability` | OPC+EXT | text | "alta", "media", "baixa", "inexistente" |
| `panel_size` | OBR (colegiado) | int | Número de membros do colegiado |
| `votes_present` | OBR (colegiado) | int | Número de votos presentes |
| `divergence_present` | REC | bool | Se houve divergência |
| `vista_present` | OPC | bool | Se houve pedido de vista |
| `destaque_present` | OPC | bool | Se houve destaque |
| `agu_manifested` | OPC | bool | Se a AGU se manifestou |
| `pgr_manifested` | OPC | bool | Se o PGR se manifestou |
| `amicus_participation` | OPC | bool | Se houve amicus curiae |
| `extraction_method` | OBR | text | "manual", "automatico", "hibrido" |
| `confidence_score` | OBR | float | 0.0 a 1.0 |

### Campos proibidos no payload

| Campo | Razão |
|---|---|
| `relator` | Modelado como edge `relator_de` |
| `composicao` | Modelado como edges `exerce_papel` |
| `subjects` | Modelados como edges `sobre` |
| `artigos_atingidos` | Modelados como edges `interpreta`/`aplica`/`questiona` |

## 2.2 `mudanca_estado`

Event class: manutencao · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `from_state` | OBR | text | Estado anterior |
| `to_state` | OBR | text | Novo estado |
| `reason` | REC | text | Justificativa da mudança |

## 2.3 `correcao`

Event class: manutencao · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `hash_anterior` | OBR | text | Hash do payload antes da correção |
| `campo_corrigido` | REC | text | Nome do campo corrigido |
| `valor_anterior` | REC | text | Valor anterior |
| `valor_novo` | REC | text | Valor novo |
| `reason` | REC | text | Justificativa |

## 2.4 `anulacao`

Event class: manutencao · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `reason` | OBR | text | Justificativa da anulação |
| `hash_anulado` | REC | text | Hash do dado anulado |

## 2.5 `criacao`

Event class: manutencao · Domain: transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `source_description` | REC | text | Descrição da fonte |
| `batch_id` | OPC | text | ID do lote de ingestão |

## 2.6 `emenda_aplicada`

Event class: normativo · Domain: normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `emenda_slug` | OBR | text | Slug da emenda constitucional |
| `action` | OBR | text | "adicionou_artigo", "adicionou_paragrafo", "alterou_texto", "revogou" |
| `node_afetado` | OBR | text | Slug do nó afetado |
| `node_adicionado` | OPC | text | Slug do nó adicionado (quando ação = adicionar) |
| `texto_anterior` | OPC | text | Texto antes da alteração |

## 2.7 `distribuicao`

Event class: juridico · Domain: juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `relator_slug` | REC | text | Slug do ministro relator |
| `classe` | REC | text | Classe processual |
| `origem` | OPC | text | Tribunal de origem |

## 2.8 `formacao_resultado`

Event class: juridico · Domain: juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| `resultado_slug` | OBR | text | Slug do objeto resultado_decisorio vinculado |
| `votos_favor` | REC | int | Votos a favor |
| `votos_contra` | REC | int | Votos contra |

---

# 3. EDGES

## 3.1 `exerce_papel`

Epistemic class: institucional · Transversal

| Campo no payload | Nível | Tipo | Descrição |
|---|---|---|---|
| `role` | OBR | text | Papel exercido |

Valores de `role` no contexto de julgamento:

| role | Obrigatoriedade |
|---|---|
| `relator` | obrigatório em todo julgamento |
| `votante` | recomendável |
| `presidente_sessao` | recomendável |
| `divergente` | quando houver |
| `autor_vista` | quando houver |
| `autor_destaque` | quando houver |
| `manifestante_agu` | quando houver |
| `manifestante_pgr` | quando houver |
| `custos_legis_manifestante` | quando houver |
| `amicus_curiae` | quando houver |

> source = actor (quem exerce) · target = object/event (onde exerce)

## 3.2 `interpreta` / `aplica` / `questiona`

Epistemic class: interpretativa · Juridico → Normativo

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| weight | OBR | float | Confidence da extração (0.0 a 1.0) |
| `extraction_method` | OBR (payload) | text | "manual", "automatico", "hibrido" |
| `citation_text` | OPC (payload) | text | Trecho que evidencia a interpretação |

> source = decisão · target = dispositivo normativo

## 3.3 `impacta_orcamento` / `aloca_risco_fiscal`

Epistemic class: fiscal · Juridico → Transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| weight | OBR | float | Magnitude do impacto (0.0 a 1.0) |
| `direcao` | OBR (payload) | text | "aumento_despesa", "reducao_receita", "neutro" |
| `estimativa_brl` | REC (payload) | numeric | Valor estimado |
| `horizonte_temporal` | REC (payload) | text | "imediato", "curto", "medio", "longo" |
| `confianca` | REC (payload) | float | Confiança na estimativa |
| `retroatividade` | OPC (payload) | bool | Se retroativo |
| `base_documental` | OPC (payload) | text | Referência |

> source = decisão · target = ente_orcamentario

## 3.4 `suporta` / `contradiz` / `fundamenta` / `apoia`

Epistemic class: argumentativa · Juridico → Juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| weight | REC | float | Força do argumento (0.0 a 1.0) |
| `ministro_slug` | OPC (payload) | text | Ministro autor do argumento |
| `context` | OPC (payload) | text | Contexto do vínculo |

> source = argumento/fundamento · target = decisão/argumento

## 3.5 `confirma` / `supera`

Epistemic class: argumentativa · Juridico → Juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| weight | REC | float | Confidence (0.0 a 1.0) |
| `extraction_method` | REC (payload) | text | Como foi identificada a confirmação/superação |

> source = decisão nova · target = decisão/tese anterior

## 3.6 `sobre`

Epistemic class: classificatoria · Transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| weight | OPC | float | Relevância do tema (0.0 a 1.0) |

> source = qualquer object · target = subject

## 3.7 `parent_of`

Epistemic class: estrutural · Transversal

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| weight | PRO | — | Não se aplica |
| payload | PRO | — | Não necessário |

> source = pai · target = filho · allows_multiple = false

## 3.8 `relator_de`

Epistemic class: institucional · Juridico → Juridico

| Campo | Nível | Tipo | Descrição |
|---|---|---|---|
| weight | PRO | — | Não se aplica |
| payload | OPC | jsonb | Contexto adicional |

> source = actor (ministro) · target = object (processo) · allows_multiple = false

---

# 4. REGRAS GERAIS

## 4.1 Campos prospectivos (EXT)

> Todo campo marcado com EXT exige no mesmo payload:
> * `extraction_method`: "manual" | "automatico" | "hibrido"
> * `confidence_score`: float 0.0 a 1.0

> Provenance deve registrar o mesmo extraction_method e confidence.

## 4.2 Campos proibidos (PRO)

> Campos PRO indicam informação que pertence a outra camada:
> * Relações → edges (não campos no payload)
> * Estado → events (não campos no object)
> * Derivados → views (não campos no primitivo)

## 4.3 Regra de rejeição do pipeline

> O pipeline deve rejeitar inserções que:
> 1. Faltem campos OBR
> 2. Contenham campos PRO
> 3. Tenham campos EXT sem extraction_method e confidence_score
> 4. Tenham weight NULL quando edge_type.weight_required = true

## 4.4 Regra de warning do pipeline

> O pipeline deve emitir warning (mas aceitar) quando:
> 1. Faltem campos REC
> 2. Campos INF não estejam preenchidos (serão derivados depois)

## 4.5 Completude mínima do julgamento colegiado

> Nenhum julgamento colegiado é considerado completo sem:
> * outcome
> * decision_body
> * adjudication_environment
> * panel_size
> * votes_present
> * extraction_method
> * confidence_score
> * Edge `relator_de` vinculado
> * Edge `exerce_papel` com role = "relator"

> Julgamentos incompletos não devem ser utilizados em views analíticas ou preditivas.

---

**DATA CONTRACT — Versão 1**
**Derivado da Constituição Ontológica v9**
**25 de março de 2026**
**Damares Medina**
