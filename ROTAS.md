# ROTAS · ICONS

**Local onde tudo começou.**
**Documento de reconstituição: 14 de abril de 2026.**
**Autora:** Damares Medina.
**Finalidade:** registrar, em prosa clara, o caminho que existiu, o que travou, o que sobreviveu e o que falta — para nunca mais perder a rota.

---

## Preâmbulo · por que este documento existe

Numa noite, aqui, neste diretório `C:\projetos\icons\`, começou o que hoje é uma linha inteira de pesquisa sobre o Supremo brasileiro, e que, na outra ponta, viraria produto no JudX.

Começou com o ato de baixar o **inteiro teor** de ~8 mil decisões do STF, ancoradas aos dispositivos da Constituição Federal de 1988. Começou com a intuição de que as decisões não existem soltas — **existem como pulsos numa corda ancorada em atores, desenho institucional e tempo**. Começou com a ideia de que o corpus, tratado com rigor ontológico, permitiria uma cartografia que ninguém havia feito.

A noite foi longa, produtiva e, ao mesmo tempo, frustrante. Os dados brutos foram extraídos e salvos em disco. Os scripts de ingestão foram escritos em camadas — parsers v4, v5, v6, v7, v8, correções, auditorias. O banco foi populado **em parte**. Mas a última ponte — **a camada semântica derivada, a que consome os embeddings** — não chegou a ser construída. E, no dia seguinte, as rotas se perderam.

Este documento reconstitui a rota.

---

## 1. Princípios ontológicos · a coluna vertebral

Estas são as cinco colunas sobre as quais todo o resto se apoia. Violar qualquer uma delas invalida o modelo.

### 1.1 Teoria dos Objetos Ancorados

O processo é uma **string** — corda tensionada que vibra. Cada recurso é uma string acoplada. Cada decisão é um **pulso** — nó nessa corda. Nenhum pulso existe isoladamente: está sempre **ancorado em três eixos simultâneos**:

- **Atores** — partes, relator, colegiado, amici, terceiros institucionais
- **Desenho institucional** — classe processual, rito, colegiado, competência, forma procedimental
- **Tempo** — protocolo, autuação, distribuição, pauta, julgamento, trânsito

Processos não são campos sem forças. Cada pulso que modelamos preserva essas três ancoragens, sob pena de destruir o objeto de análise.

### 1.2 Anatomia do acórdão e da decisão

- **Monocrática** = um ministro. **Colegiada** = órgão.
- **Acórdão virtual** em regra traz apenas o voto do relator; demais votam "com o relator". É **materialmente monocrático e formalmente colegiado**. A distinção precisa estar explícita nos metadados de cada pulso.
- **Inflexão virtual × presencial** — concomitante à pandemia, o STF passou a julgar virtualmente e nunca mais voltou. Essa inflexão é **dado**, não contexto.
- **Extrato da ata** (último, quando há vários) é o documento de fechamento: venceu, vencido, vista, início e fim do julgamento.
- **Vida do processo ≠ decisão.** A decisão é o resultado. A vida é o percurso — e diz tudo.
- **Relator quase nunca perde no STF**, sobretudo no virtual. Esse dado precisa ser legível no modelo.

### 1.3 Carta fundante JudX × ICONS

Decisão de 14/abr/2026. Documento-mãe em `C:\Users\medin\Desktop\JUDX_ICONS_CARTA_FUNDANTE.md`.

- **ICONS** produz: corpus, ontologia, embeddings, teoria, protocolo, cartografia, papers.
- **JudX** consome via API: dashboard, perfil decisório, alerta, prognóstico, assinatura.

Este ROTAS pertence ao **ICONS** — é obra de pesquisa.

### 1.4 A fonte é clara; o modelo é que não soube ler

A obra *A Constituição e o Supremo* já é estruturalmente clara:

- **Identação hierárquica** marca visualmente o nível (caput → inciso → alínea → parágrafo)
- **Separadores editoriais** (Súmula Vinculante, Súmula, Controle Concentrado, Repercussão Geral, Julgados Correlatos) segmentam o que pertence a cada dispositivo
- **Label final do processo** (ADPF 1234 RJ, rel. min. Fulano, j. 00/00/0000, DJE 00/00/0000) em padrão fixo e reconhecível

O leitor humano resolve a ancoragem sem esforço. Quando o parser falha, a falha é do **parser**, nunca da fonte. Proibido atribuir ao STF dificuldade que é técnica.

### 1.5 Biografia ≠ Doutrina

Duas noções de "linha" completamente diferentes. Nunca confundir.

- **Linha da vida do processo** (`processo_linha_decisoria`, 2.927.914 linhas) — sequência temporal de atos **dentro de um mesmo processo**. Termina quando transita em julgado ou é arquivado. É **biografia**. Projeto pronto, não é experimento, não será aposentado.
- **Linha jurisprudencial** (`judx_decision_line`, camada derivada a construir) — sequência temporal de entendimentos sobre o mesmo **tema × sub-dispositivo**, atravessando múltiplos processos, relatores, décadas. É **doutrina**.

> **A primeira é biografia. A segunda é doutrina.**

---

## 2. Consequências ontológicas que atravessam tudo

### 2.1 Cardinalidade 1:N entre processo e sub-dispositivo

Um acórdão (ADI, ADPF, RE, ARE) ancora em **múltiplos sub-dispositivos** na mesma peça. A relação processo → dispositivo é **1:N, não 1:1**.

A tabela N:M que sustenta isso é `judx_decision_line_case` (`case_id × decision_id × decision_line_id` + `line_position` + `environmental_transition_relevance`). Mesmo texto, quando ancora em N sub-dispositivos, gera **N chunks** — um por ancoragem.

### 2.2 Ancoragem granular · a coluna vertebral de cada métrica

O grão mínimo da análise é `(artigo, sub-dispositivo canônico)`. Ancorar em "art. 5º" é afogar histórias jurisprudenciais completamente distintas numa média vazia.

Slugs canônicos:

- `cf-1988-art-5` (caput)
- `cf-1988-art-5-inc-xxxiv-ali-a`
- `cf-1988-art-37-par-6`
- `cf-1988-art-150-inc-iii-ali-b`
- `adct-art-68`

A árvore é irregular (inciso pode ter alínea; parágrafo pode ter inciso; alínea pode estar no caput), mas **explícita na identação da obra**. Parser que respeita identação como árvore ancora corretamente.

Qualidade da ancoragem viaja como metadado:

- `exata` — declarada na identação ou no cabeçalho editorial
- `contextual` — inferível por proximidade textual (parágrafo imediatamente acima declara)
- `inferida` — análise posterior determinou por similaridade
- `generica_nao_resolvida` — só ancorado no artigo; fica em fila de re-ancoragem

### 2.3 Revisita ≠ virada

O STF revisita temas o tempo todo. **Troca de relator é sinal contextual, não diagnóstico.**

Virada jurisprudencial é **evento inferido**, não extraído. Requer:

- **Tempo** — par ordenado de doutrinas sucessivas, por data de julgamento
- **Conteúdo** — divergência semântica entre doutrinas sucessivas da mesma linha
- **Persistência** — a divergência se mantém nas janelas seguintes; virada episódica não conta

Relatoria entra como **variável explicativa posterior**: depois de detectada a virada, investiga-se correlação com troca de relator, novo colegiado, mudança de ambiente, composição nova da Corte. Mas a virada não é a troca — é o que a troca eventualmente produziu, quando produziu.

### 2.4 ICONS produz / JudX monta

A ponte que falta **não termina em `public.embeddings` do ICONS**. Ela entrega ao JudX, que monta a trilha jurisprudencial populando `judx_decision_line` + `judx_decision_line_case` usando:

- Embeddings ancorados do ICONS
- Similaridade semântica entre doutrinas sucessivas
- Assinatura ambiental (virtual × presencial × convertido)
- Evolução por sub-dispositivo granular

---

## 3. Estado atual (abril de 2026)

### 3.1 Dados em disco (intactos) — `C:\projetos\icons\ingest\`

| Arquivo | Linhas | Conteúdo |
|---|---|---|
| `decision_blocks_resolved.tsv` | 11.035 | Blocos com `block_text`, `anchor_slug`, metadados processuais completos |
| `commentary_blocks.tsv` | 10.812 | Blocos de comentário associados |
| `stf_metadata_confirmada.tsv` | 7.751 | Metadados processuais confirmados |
| `07_processos_urls.csv` | 1.994 | URLs de peças |
| `08_processos_metadados.csv` | 6.236 | Metadados processuais |
| `05_acoes_stf.csv` | 8.193 | Processos referenciados |
| `stf_hierarchy.json` | 3,4 MB | Árvore normativa da CF |
| `commentary_blocks.json` | 9,8 MB | JSON espelho |
| `stf_constituicao_raw.html` | 37,5 KB | HTML oficial do STF (ground truth) |

Redundância garantida no git do repositório `icons-cartografia` (commit `f9b32a5`, 06/abr/2026).

### 3.2 Supabase ICONS (`hetuhkhhppxjliiaerlu`) — populado

| Tabela | Registros |
|---|---|
| `edges` | **473.853** |
| `objects` | **252.481** |
| `provenance` | **203.082** |
| `marcadores_unidade` | 15.188 |
| `unidades_decisorias` | **7.766** |
| `stf_metadados_confirmados` | 7.750 |
| `grupos_editoriais` | 2.155 |
| `actors` | 100 |
| Taxonomias | `edge_types` 36, `object_types` 31, `event_types` 14, `actor_types` 9, `domains` 9 |

**Vazias (camadas derivadas a construir):** `chunks`, `embeddings`, `published_objects`, `learned_decision_profiles`, `ledger`, `legal_events`, `positions`, `markets`, `resolutions`.

### 3.3 Supabase JudX (`ejwyguskoiraredinqmb`) — referência cruzada (pertence ao lado JudX)

| Tabela | Registros | Papel |
|---|---|---|
| `judx_decision` | **2.927.525** | Pulso individual com marcadores ricos (kind, technique, result, ambiente virtual/presencial/convertido, unanimidade, fragmentação colegiada, densidade argumentativa) |
| `processo_linha_decisoria` | **2.927.914** | **Biografia do processo** — projeto pronto |
| `judx_decision_line` | 0 | **Doutrina no tempo** — camada derivada |
| `judx_decision_line_case` | 0 | N:M (case × decision × line) — camada derivada |

### 3.4 Conclusão sobre o estado

**Não é preciso re-executar nada da ingestão.** Os dados já chegaram ao Supabase por caminho que funcionou. A tarefa é construir a **ponte da camada semântica derivada** — chunks → embeddings → alimentação da doutrina.

---

## 4. Arqueologia dos scripts (`C:\projetos\icons\ingest\`)

Os scripts existem em versões porque o problema foi compreendido em camadas.

### 4.1 Parsers (`parser_v4` → `parser_v8`)

Lêem o `.docx` da Constituição Comentada do STF e o HTML oficial, extraem blocos com regex para classe, relator, redator, julgamento, DJE, tema RG, súmula. Produzem `commentary_blocks.json` e `decision_blocks_resolved.tsv`. **Referência atual:** `parser_v8.py`.

### 4.2 Sincronização com o STF (`sync_with_stf.py`, `sync_with_stf_v2.py`, `sync_final.py`)

Usam o HTML oficial como ground truth para reancorar blocos. Resolvem divergência entre obra editorial e portal oficial.

### 4.3 Importação direta (`import_stf_direct.py`, `import_stf_hierarchical.py`) — **TRAVARAM, NÃO RE-EXECUTAR**

Ver Seção 5 para diagnóstico. Os dados que esses scripts tentavam popular já estão no Supabase por outro caminho. **Proibido re-executar** sem antes revisar os anti-padrões documentados na Seção 5.

### 4.4 Construção de blocos (`build_decision_blocks.py`)

Versão 2.3. Consolida `decision_blocks_unified`, aplica `anchor_slug_final` com fallback de qualidade/confiança.

### 4.5 Correções incrementais

`resolve_v2_2b.py` (refs + hash sha256), `unify_anchors.py` (âncoras ambíguas), `fix_dedup_and_coanchors.py`, `fix_fronteiras.py`, `fix_text_quality.py`.

### 4.6 Auditorias (`gen_audit_*.py`)

HTMLs de inspeção visual para validação humana.

### 4.7 Carga (`populate_db.py`)

Lê `commentary_blocks.json` + `norm_anchor_index.tsv` → SQLite ou Postgres.

---

## 5. Os cinco anti-padrões que travaram a noite

Documentados aqui para que **nunca mais** o mesmo padrão se repita em nenhum script do ICONS.

### 5.1 Insert em loop sem transação explícita

**Anti-padrão:** `for b in blocks: con.execute(insert_sql, values)` — commit implícito a cada linha. 8.903 commits → ~15 min parecendo travado.

**Regra:** `BEGIN TRANSACTION` + loop + `COMMIT`, ou `executemany` em lotes de 500-1.000.

### 5.2 Operação destrutiva sem idempotência

**Anti-padrão:** `ALTER TABLE ... RENAME TO _backup` + `CREATE TABLE` — na segunda execução, `_backup` já existe e o script morre sem mensagem útil.

**Regra:** `DROP TABLE IF EXISTS` ou, melhor, gravar em tabela nova e fazer a troca atômica no final. Toda operação destrutiva tem rollback planejado.

### 5.3 Rebuild de tabela derivada sem índice durante a carga

**Anti-padrão:** `INSERT INTO ... SELECT` em 8.903 linhas sem índice auxiliar → O(n²).

**Regra:** índices **depois** da carga, mas com progresso reportado a cada N linhas.

### 5.4 Scripts "one-shot" não idempotentes

**Anti-padrão:** script feito para rodar uma única vez, sem verificação de estado.

**Regra:** `INSERT OR IGNORE`, `ON CONFLICT DO NOTHING`, `UPSERT`. Re-executar deve ser **seguro**.

### 5.5 Ausência de log visível

**Anti-padrão:** nenhum `print` intermediário. "Travado" e "lento" ficam indistinguíveis.

**Regra:** progresso a cada 100-500 linhas. Mensagem final com contagem. Se falhar, mensagem clara do erro e onde parou.

---

## 6. A ponte que falta · `unidades_decisorias → chunks → embeddings → doutrina`

Esta é a única camada a construir. Sai do Supabase ICONS, não do SQLite local.

### 6.1 Entrada

- **Fonte:** `unidades_decisorias` no ICONS (7.766 registros)
- **Joins:** `marcadores_unidade`, `edges` (ancoragem granular), `stf_metadados_confirmados`, `actors`
- **Referência cruzada:** `judx_decision` e `processo_linha_decisoria` no JudX, para preservar o ancoramento biográfico (qual decisão, qual posição na vida do processo)

### 6.2 Chunker ontológico

Cada chunk é um **objeto ancorado**. Cardinalidade: uma unidade pode gerar **N chunks** (um por sub-dispositivo atacado — 1:N da Seção 2.1).

Metadados que **obrigatoriamente** viajam com o vetor:

| Campo | Origem | Função |
|---|---|---|
| `anchor_slug` | edges / stf_hierarchy | ancoragem normativa granular (`cf-1988-art-5-inc-lv`) |
| `anchor_depth` | derivado do slug | `artigo`, `caput`, `inciso`, `paragrafo`, `alinea`, `composto` |
| `anchor_quality` | parser + inferência | `exata` \| `contextual` \| `inferida` \| `generica` |
| `anchor_co_anchors` | edges | outros sub-dispositivos citados na mesma peça |
| `process_class`, `process_number` | stf_metadados_confirmados | ancoragem processual |
| `process_id` | judx_case | link à biografia do processo (Seção 1.5) |
| `relator`, `redator` | stf_metadados_confirmados | ancoragem de ator |
| `julgamento_data`, `dje_data` | stf_metadados_confirmados | ancoragem temporal |
| `decision_unit_type` | parser_v8 | natureza (monocrática × colegiada; virtual × presencial quando inferível) |
| `editorial_marker` | parser_v8 | SV > Súmula > Controle Concentrado > RG > Correlatos |
| `chunk_source` | chunker | `doctrine`, `ementa`, `voto_relator`, `extrato_ata`, `outro` |

### 6.3 Granularidade do chunk — decisão a tomar em sessão separada

| Candidato | Chunks | Custo estimado (text-embedding-3-small) | Uso |
|---|---|---|---|
| **doctrine** (≤119 chars) | ~2.800 | ~US$ 0,02 | cartografia de regimes |
| **unidade_decisoria** integral | ~7.766 | ~US$ 1-3 | buscador de casos similares |
| **parágrafo/bloco médio** | 30-80k | ~US$ 5-20 | retrieval cirúrgico, RAG |

A regra ontológica da Seção 1.1 exige que a escolha preserve a ancoragem tripla. Decisão a tomar em sessão específica.

### 6.4 Modelo de embedding

- **Preferencial:** OpenAI `text-embedding-3-small` (1536 dimensões)
- **Schema compatível:** `public.embeddings.vector_ref vector(1536)` já criado
- **Chave:** comprada — confirmar saldo antes de executar

### 6.5 Saída imediata (ICONS)

Tabela `public.embeddings`:

| Coluna | Conteúdo |
|---|---|
| `id` | bigint pk |
| `chunk_slug` | canônico e legível (ex: `cf-1988-art-5-inc-lv/adi-4277/2011-05-05/doctrine-01`) |
| `embedding_model` | `openai-text-embedding-3-small` |
| `vector_ref` | vector(1536) |
| `court_id` | STF |
| `created_at` | timestamptz |

### 6.6 Saída derivada (JudX)

A partir dos embeddings ancorados, o JudX popula:

- `judx_decision_line` — estado da trilha por (tema, sub-dispositivo), detectando virada por **divergência semântica persistente** entre doutrinas sucessivas (Seção 2.3)
- `judx_decision_line_case` — N:M que casa cada decisão às trilhas que ela alimenta

**ICONS produz o vetor; JudX monta a trilha.** Conforme carta fundante.

---

## 7. Ordem de execução segura

> *Só executar quando houver decisão sobre granularidade do chunk e confirmação de saldo na chave OpenAI.*

1. **Pré-voo**
   - Saldo OpenAI confirmado
   - Conexão Supabase ICONS testada
   - Backup da tabela `embeddings` (vazia hoje, mas higiene é obrigatória)

2. **Dry-run (sem gastar)**
   - Pipeline sobre **10 unidades** de amostra
   - Chunks gerados em arquivo local, sem chamar OpenAI
   - Inspeção manual: slug canônico, metadados íntegros, ancoragem tripla preservada
   - **Só prosseguir se as 10 amostras estiverem íntegras**

3. **Execução em lotes pequenos**
   - Lote 1: 100 unidades → custo real × estimado
   - Verificar que `public.embeddings` recebeu o esperado
   - Expansão: 1.000 → total

4. **Checkpoint final**
   - Contagem: `unidades × chunks_por_unidade_esperados = embeddings_gravados`?
   - Amostra aleatória de 20 vetores — metadados corretos?
   - Teste de similaridade: textos próximos têm vetores próximos?

5. **Registro**
   - Atualizar este `ROTAS.md` com data, resultado, custo real (emenda datada no final)
   - Commit em git

---

## 8. Princípios operacionais gravados

1. **O objeto não precede o processo. É produzido por ele.** Todo chunk preserva ancoragem tripla: ator × desenho × tempo.
2. **Monocrática ≠ colegiada; virtual ≠ presencial.** Metadados marcam a distinção em cada pulso.
3. **Biografia ≠ Doutrina.** Nunca confundir `processo_linha_decisoria` com `judx_decision_line`.
4. **Fonte é clara; falha é do modelo.** Proibido atribuir à obra editorial dificuldade que é de parser.
5. **Revisita ≠ virada.** Relatoria é sinal contextual; virada exige tempo + conteúdo + persistência.
6. **Ancoragem granular é coluna vertebral.** Grão mínimo: sub-dispositivo.
7. **1:N real.** Mesmo texto, múltiplas ancoragens, múltiplos chunks.
8. **ICONS produz; JudX monta.** A ponte entrega o vetor; a trilha se monta no produto.
9. **Rotas se perdem mais rápido que dados.** Este documento é memória externa.
10. **Scripts idempotentes, com log, em transação.** Nunca mais travar em silêncio.

---

## 9. O que este documento não é

Não é plano de implementação. Não é especificação técnica. Não é código.

É uma **carta de reconstituição**. Uma ponte entre a noite em que tudo começou e o dia em que for retomado — seja por mim, seja por quem me suceder na coordenação do ICONS.

Se você abrir este arquivo daqui a seis meses e tudo parecer confuso, comece pela **Seção 1** (princípios) e pela **Seção 3** (estado atual). O resto ilumina essas duas.

---

*Documento vivo. Emendas sempre datadas, no final. Nunca apagar seções.*

---

## Emendas posteriores

### Emenda 01 · 14/abr/2026 · Fundação da Cartografia

Na mesma noite em que este documento foi escrito, a fundação foi executada. Registro do que aconteceu:

**1. Recuperação das datas perdidas.**
A suspeita de Damares de que o TSV em disco tinha dados que o Supabase não tinha estava correta. O banco tinha 32,5% das unidades com data; o TSV tinha 80%. Foi construída `staging_tsv_datas` com 6.529 linhas extraídas do TSV, e um UPDATE seletivo trouxe a cobertura de `unidades_decisorias.data_julgamento_iso` para **81,6% (6.340/7.766)**. Corpus datado de **1988-10-20 a 2026-02-25**.

**2. Regra geral do ICONS confirmada.** *A fonte é clara; o modelo é que não soube ler.* O Supabase foi alimentado por deploy parcial do parser original, perdendo dados que o TSV já tinha. Nunca mais presumir o banco como espelho fiel dos arquivos em disco sem verificar.

**3. Cartografia populada — 849 chunks fundadores.**
Cada chunk é um dispositivo constitucional com corpus cronologicamente ordenado das decisões que o ancoram. Distribuição por profundidade:

- `artigo`: 189 (maior: `cf-1988-art-5` com 1.049 pulsos)
- `paragrafo`: 167
- `inciso`: 391
- `alinea`: 88
- `outro`: 14

**4. Granulação inferida — +91 chunks novos.**
Análise por regex identificou 402 reancoragens em 367 unidades cujo conteúdo menciona sub-dispositivo específico (ex: "art. 55, VI", "art. 102, II, a"). Criados 91 chunks granulares novos com `metadata.anchor_quality = 'inferida'` e 86 objects novos em `public.objects`. Os 49 chunks-pai afetados foram marcados com `has_granular_children: true`. **Dupla ancoragem preservada:** cada unidade reancorada fica tanto no chunk formal quanto no chunk granular inferido.

Total final: **940 chunks** na tabela `chunks`.

**5. A alavanca descoberta — alocação em massa.**
Damares percebeu que as 940 placas, uma vez embedadas, viram um sistema de coordenadas capaz de alocar as 2.927.525 decisões do `stf_master_premium` por similaridade vetorial. Plano de alocação em massa registrado abaixo (Seção: **Alocação em massa via similaridade**).

**6. Backup completo.**
`C:\projetos\icons\backups\2026-04-14_sismografo_fundacional\` com 15.723 linhas em 5 CSVs + `ESTADO_BANCO.md`. Se o Supabase evaporar, a restauração é direta.

**7. Script de Fase 1 pronto.**
`C:\projetos\icons\scripts\generate_embeddings_fase1_placas.py` — idempotente, com log, com dry-run, com recuperação de falha. Espera variável `OPENAI_API_KEY`. Custo estimado Fase 1 (940 placas): ~US$ 0,10.

---

## Alocação em massa via similaridade · plano de Fase 2

**Descoberta de Damares, 14/abr/2026.**

As 940 placas populadas hoje são uma **estrutura de ancoragem universal**. Cada placa tem corpus doutrinário agregado. Cada uma das 2.927.525 decisões do `stf_master_premium` (JudX) pode ser **situada contra esse mapa** via similaridade vetorial.

### Arquitetura

```
ICONS (universo ancorado)
  ↓
  940 chunks (placas) · embedding do corpus agregado
  ↓  cosine similarity
JUDX (stf_master_premium · 2,9M decisões)
  ↓
  cada decisão → k placas mais próximas + score
  ↓
  gravar em judx_decision_line_case (N:M)
  ↓
JUDX monta judx_decision_line com milhões de pulsos
  ↓
Sismógrafo jurisprudencial em escala real
```

### Fases e custos

| Fase | Escopo | Tokens | Custo estimado |
|---|---|---|---|
| **Fase 1** | Embedar 940 placas (ICONS) | ~4,7M | ~US$ 0,10 |
| **Fase 2a** | Embedar 100 mil decisões (amostra estratificada do JudX) | ~50M | ~US$ 1,00 |
| **Fase 2b** | Embedar todas 2,9M decisões do master premium | ~1,45B | ~US$ 29,00 |
| **Fase 3** | Computar similaridades e popular `judx_decision_line_case` | — | US$ 0 (local) |
| **Fase 4** | Consolidar `judx_decision_line` e estados de linha | — | US$ 0 |

### Três problemas que a alocação resolve de uma vez

1. **Granulação em escala.** 189 chunks ainda em "artigo inteiro" ganham filhos granulares com evidência vetorial, não apenas regex.
2. **Completamento temporal.** `stf_master` tem 100% de data; Cartografia hoje tem 81,6%. Alocar decisões datadas eleva a densidade cronológica em ordens de grandeza.
3. **Revisita × virada com rigor.** Com milhares de pulsos datados por placa, a detecção de virada deixa de depender de amostras pequenas e vira estatisticamente sólida.

### Pré-condições antes de executar Fase 2

1. Fase 1 concluída (placas embedadas)
2. Saldo confirmado na chave OpenAI (US$ 30 mínimo para Fase 2b completa)
3. Schema `judx_decision_line_case` confirmado no JudX (já validado em 14/abr)
4. Dry-run com 1.000 decisões primeiro, inspeção manual dos scores, expansão gradual

### Princípios operacionais para Fase 2

- Usar `text-embedding-3-small` (mesmo modelo da Fase 1, para vetores comparáveis)
- Chunking por decisão = ementa + primeiros 2 parágrafos do voto do relator (se disponível), limitado a 8191 tokens
- Para cada decisão: top-5 placas por cosine similarity, com score
- Se score < threshold (a calibrar, ex: 0,75), decisão fica em fila de "não ancorável" — não forçar alocação fraca
- Metadados que viajam com a alocação: score, rank, método, data da computação

