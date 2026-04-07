# EMENDA CONSTITUCIONAL Nº 01

## Dupla Ancoragem — Sistema Judicial

**Autora:** Damares Medina
**Data:** 2026-03-26
**Base:** CONSTITUIÇÃO ONTOLÓGICA v1 (congelada 25/03/2026)
**Status:** APROVADA — 2026-03-26

---

## 1. MOTIVAÇÃO

O sistema modela a relação entre o ordenamento normativo e o exercício jurisdicional. A Constituição Federal é a âncora normativa primária. O STF é a âncora jurisprudencial primária. Entre eles existe um espaço interpretativo ocupado por decisões.

Na v1, esse espaço é modelado como `anotacao` (editorial) subordinada ao dispositivo normativo. A decisão não tem existência própria — é apêndice do artigo.

Na realidade, o sistema judicial opera em dois eixos simultâneos:

- **Eixo normativo**: Art. 5º, inc. X → interpretado por N decisões
- **Eixo jurisprudencial**: ADI 4.277 → incide sobre N dispositivos

A decisão está ancorada nos dois eixos ao mesmo tempo. Essa dupla ancoragem é o mecanismo central do sistema.

A expansão para STJ, TRFs e outros tribunais exige que toda decisão entre na mesma estrutura, com ancoragem normativa e identidade jurisprudencial própria, sem alterar a ontologia.

---

## 2. NOMENCLATURA

O projeto adota terminologia própria, alinhada ao seu objeto:

| Termo anterior | Termo ICONS | Significado |
|---|---|---|
| commentary_block | **registro_jurisprudencial** | unidade base do eixo jurisprudencial — trecho decisório ancorado a dispositivo |
| editorial_marker | **camada_editorial** | posição hierárquica da decisão dentro do dispositivo (SV, Súmula, CC, RG, JC) |
| decision_unit_type | **tipo_decisorio** | natureza da unidade (súmula vinculante, controle concentrado, etc.) |
| anchor_slug | **ancora_normativa** | slug do dispositivo constitucional ao qual o registro se vincula |
| process_key | **ancora_processual** | identificador do processo judicial (classe + número) |
| block_text | **conteudo** | texto da ementa ou trecho decisório |
| metadata_text | **rotulo_final** | referência bibliográfica da decisão |
| normative_text | **texto_dispositivo** | texto do dispositivo constitucional |
| marcador_editorial | **divisor_editorial** | marcador de início de camada editorial dentro do dispositivo |

### Glossário estrutural

| Conceito | Definição |
|---|---|
| **ancora_normativa** | vínculo de um registro jurisprudencial a um dispositivo da CF/ADCT |
| **ancora_processual** | identidade do processo judicial que originou o registro |
| **ancoragem_sistemica** | a relação bidirecional dispositivo ↔ decisão que constitui o eixo interpretativo |
| **registro_jurisprudencial** | a menor unidade autônoma do sistema: um trecho decisório com âncora normativa, camada editorial, metadados e conteúdo |
| **camada_editorial** | a hierarquia interna de cada dispositivo: SV > Súmula > CC > RG > JC |
| **divisor_editorial** | marcador estrutural que separa as camadas dentro de um dispositivo |

---

## 3. ESTRUTURA DO SISTEMA JUDICIAL

```text
SISTEMA JUDICIAL

1. NÚCLEO PRIMÁRIO DE ANCORAGEM

   1.1 ÂNCORA NORMATIVA PRIMÁRIA
       └── Constituição Federal de 1988
            └── hierarquia dispositiva:
                art → § → inc → ali → item
            └── ADCT (mesma hierarquia)

   1.2 ÂNCORA JURISPRUDENCIAL PRIMÁRIA
       └── Supremo Tribunal Federal
            └── processos:
                ADI · ADC · ADPF · ADO · RE · ARE · HC · MS · Rcl · ...

2. MECANISMO CENTRAL

   2.1 ANCORAGEM SISTÊMICA (dupla ancoragem)
       └── registro_jurisprudencial
            ├── ancora_normativa  → dispositivo da CF
            └── ancora_processual → processo no tribunal

3. EIXO JURISPRUDENCIAL (ocupação do espaço normativo)

   3.1 UNIDADE BASE — registro_jurisprudencial
       ├── ancora_normativa     (slug do dispositivo)
       ├── camada_editorial     (SV / Súmula / CC / RG / JC)
       ├── tipo_decisorio       (classificação da unidade)
       ├── conteudo             (texto decisório)
       ├── rotulo_final         (referência bibliográfica)
       └── metadados processuais
            ├── classe · número · relator · redator
            ├── turma · data_julgamento · dje
            ├── tema_rg · sumula_num
            └── url_inteiro_teor

   3.2 CAMADAS EDITORIAIS (hierarquia fixa — ordem de exibição)
       1. Súmula Vinculante
       2. Súmula
       3. Controle Concentrado
       4. Repercussão Geral
       5. Julgados Correlatos

   3.3 DIVISOR EDITORIAL
       └── marcador estrutural que separa camadas dentro do dispositivo
            (não tem conteúdo decisório, apenas sinaliza início de camada)

4. EIXO PROCESSUAL (identidade autônoma da decisão)

   4.1 PROCESSO JUDICIAL — object (tipo: processo)
       ├── slug: {tribunal}-{classe}-{numero}
       ├── classe · número · tribunal
       ├── relator · redator · turma
       ├── datas (julgamento, publicação)
       ├── tema_rg · merito_status
       └── url_inteiro_teor

   4.2 UM PROCESSO → N REGISTROS JURISPRUDENCIAIS
       └── ADI 4.277 pode ter blocos em:
            ├── cf-1988-art-5 (caput)
            ├── cf-1988-art-226-par-3
            └── cf-1988-art-3-inc-iv

   4.3 UM DISPOSITIVO → N PROCESSOS
       └── cf-1988-art-5-inc-x pode ser interpretado por:
            ├── stf-adi-4277
            ├── stf-re-477554
            └── stj-resp-1234567 (futuro)

5. EXPANSÃO DO SISTEMA (sem alterar ontologia)

   5.1 TRIBUNAIS — entram como novos actors + objects
       ├── STJ → stj-resp-{N}, stj-agint-{N}
       ├── TRFs → trf1-ac-{N}, trf3-ai-{N}
       ├── TJs → tjsp-ac-{N}, tjrj-ms-{N}
       └── TST, TSE, STM, TCU...

   5.2 NORMAS CORRELATAS — entram como novos objects (domínio normativo)
       ├── leis federais → lei-{numero}-{ano}
       ├── leis complementares → lc-{numero}-{ano}
       ├── códigos → cc-2002, cpc-2015, cp-1940
       └── decretos → decreto-{numero}-{ano}

   5.3 PRINCÍPIO DE EXPANSÃO
       └── todo novo objeto entra por:
            ├── ancora_normativa     (qual dispositivo interpreta)
            ├── ancora_processual    (qual processo originou)
            └── vinculo_precedente   (que decisão cita/supera/confirma)
```

---

## 4. MAPEAMENTO ONTOLÓGICO

### 4.1 Novos object_types

| type_slug | domain | ontological_class | label |
|---|---|---|---|
| `registro_jurisprudencial` | juridico | editorial | Registro jurisprudencial — unidade base do eixo interpretativo |
| `processo` | juridico | processual | Processo judicial com identidade autônoma |
| `divisor_editorial` | juridico | editorial | Marcador de início de camada editorial |

> `registro_jurisprudencial` substitui `anotacao` como type para os blocos decisórios.
> `processo` é a entidade autônoma do eixo processual (ADI 4.277, RE 638.115).
> `divisor_editorial` é o marcador estrutural sem conteúdo decisório.

### 4.2 Novos edge_types

| type_slug | source | target | epistemic | mult | weight_sem | w_req | label |
|---|---|---|---|---|---|---|---|
| `ancora_normativa` | juridico | normativo | interpretativa | true | confidence (0-1) | true | registro incide sobre dispositivo |
| `ancora_processual` | juridico | juridico | estrutural | true | NULL | false | registro pertence a processo |
| `cita` | juridico | juridico | argumentativa | true | forca (0-1) | false | decisão cita precedente |
| `supera` | juridico | juridico | argumentativa | true | confidence (0-1) | false | decisão supera entendimento anterior |
| `confirma` | juridico | juridico | argumentativa | true | confidence (0-1) | false | decisão confirma precedente |
| `fixa_tese` | juridico | juridico | interpretativa | false | NULL | false | decisão fixa tese vinculante |
| `produzido_por` | juridico | juridico | institucional | false | NULL | false | processo produzido por tribunal |

> `ancora_normativa` como edge: source = registro/processo, target = dispositivo.
> `ancora_processual` como edge: source = registro, target = processo.

### 4.3 Payload do edge `ancora_normativa`

```json
{
  "camada_editorial": "controle_concentrado",
  "ordem_editorial": 3,
  "qualidade_ancora": "exact",
  "fonte_ancora": "stf_html",
  "tribunal": "stf"
}
```

### 4.4 Payload do object `processo`

```json
{
  "classe": "ADI",
  "numero": "4277",
  "processo_completo": "ADI 4.277",
  "tribunal": "stf",
  "relator": "Ayres Britto",
  "redator": null,
  "turma": "Plenário",
  "data_julgamento": "2011-05-05",
  "data_publicacao": "2011-10-14",
  "tema_rg": null,
  "sumula_num": null,
  "sumula_tipo": null,
  "merito": "julgado",
  "url_inteiro_teor": "http://redir.stf.jus.br/..."
}
```

### 4.5 Payload do object `registro_jurisprudencial`

```json
{
  "conteudo": "Reconhecimento do direito à preferência sexual...",
  "rotulo_final": "ADI 4.277, rel. min. Ayres Britto, j. 5-5-2011, P, DJE de 14-10-2011.",
  "camada_editorial": "controle_concentrado",
  "ordem_editorial": 3,
  "tipo_decisorio": "controle_concentrado",
  "stf_com_id": 86176,
  "fonte": "stf_import"
}
```

### 4.6 Novos actor_types

| type_slug | domain | actor_class | label |
|---|---|---|---|
| `tribunal` | juridico | institucional | Tribunal |
| `turma` | juridico | institucional | Turma / Órgão julgador |

### 4.7 Novos state_types

| state | object_type | domain | terminal |
|---|---|---|---|
| `pendente` | processo | juridico | false |
| `pautado` | processo | juridico | false |
| `julgado` | processo | juridico | false |
| `publicado` | processo | juridico | false |
| `transitado` | processo | juridico | true |
| `superado` | processo | juridico | true |

---

## 5. SLUG CONVENTION

### Processos

```
{tribunal}-{classe}-{numero}
```

| Slug | Processo |
|---|---|
| `stf-adi-4277` | ADI 4.277 (STF) |
| `stf-re-638115` | RE 638.115 (STF) |
| `stf-sv-37` | Súmula Vinculante 37 |
| `stf-sumula-649` | Súmula STF 649 |
| `stj-resp-1234567` | REsp 1.234.567 (STJ) |
| `tst-rr-100200` | RR 100.200 (TST) |

### Registros jurisprudenciais

```
{processo_slug}-rj-{N}
```

| Slug | Registro |
|---|---|
| `stf-adi-4277-rj-1` | 1º registro da ADI 4.277 |
| `stf-re-638115-rj-3` | 3º registro do RE 638.115 |

### Tribunais e turmas

```
tribunal-{sigla}
turma-{tribunal}-{id}
```

| Slug | Ator |
|---|---|
| `tribunal-stf` | Supremo Tribunal Federal |
| `tribunal-stj` | Superior Tribunal de Justiça |
| `turma-stf-1` | 1ª Turma STF |
| `turma-stf-plenario` | Plenário STF |

### Dispositivos normativos (mantidos)

```
cf-1988-art-{N}[-par-{X}][-inc-{Y}][-ali-{Z}]
adct-art-{N}[-par-{X}][-inc-{Y}][-ali-{Z}]
```

---

## 6. DIAGRAMA — DUPLA ANCORAGEM EM AÇÃO

```text
                    EIXO NORMATIVO                        EIXO JURISPRUDENCIAL
                    ──────────────                        ────────────────────

objects (normativo)                     edges                    objects (juridico)
┌─────────────────────────┐                                ┌──────────────────────┐
│ cf-1988-art-226-par-3   │ ←── ancora_normativa ────────  │ stf-adi-4277-rj-1    │
│ type: paragrafo         │                                │ type: registro_jurisp │
│                         │                                │ payload:              │
│                         │                                │   conteudo: "..."     │
│                         │                                │   camada: CC          │
│                         │                                │   rotulo: "ADI 4.277  │
│                         │                                │     rel. min..."      │
└─────────────────────────┘                                └──────────┬───────────┘
                                                                      │
┌─────────────────────────┐                                           │
│ cf-1988-art-5-inc-x     │ ←── ancora_normativa ────────             │ ancora_processual
│ type: inciso            │                          │                │
└─────────────────────────┘                          │                ▼
                                                     │   ┌──────────────────────┐
┌─────────────────────────┐                          │   │ stf-adi-4277         │
│ cf-1988-art-3-inc-iv    │ ←── ancora_normativa ──  │   │ type: processo       │
│ type: inciso            │                          │   │ payload:             │
└─────────────────────────┘                          │   │   classe: ADI        │
                                                     │   │   numero: 4277       │
                                                     │   │   relator: Ayres..   │
                                                     │   │   turma: Plenário    │
                                                     │   │   data: 2011-05-05   │
                                                     │   └──────────┬───────────┘
                                                     │              │
                                                     │              │ relator_de
                                                     │              ▼
                                                     │   ┌──────────────────────┐
                                                     └── │ min-ayres-britto     │
                                                         │ type: ministro_stf   │
                                                         └──────────────────────┘

  1 processo → N registros → N dispositivos
  1 dispositivo ← N registros ← N processos
```

---

## 7. MIGRAÇÃO DO BANCO ATUAL

| Campo atual (icons-db) | Destino (dupla ancoragem) |
|---|---|
| bloco com `process_key` | object `processo` (1 por process_key único) |
| cada row em `decision_blocks_resolved` | object `registro_jurisprudencial` |
| `anchor_slug` | edge `ancora_normativa` (registro → dispositivo) |
| `process_key` | edge `ancora_processual` (registro → processo) |
| `relator` | edge `relator_de` (actor → processo) |
| `editorial_marker` | payload do edge `ancora_normativa` |
| `block_text` | payload.conteudo do registro |
| `metadata_text` | payload.rotulo_final do registro |
| co-âncoras (`block_anchors`) | múltiplos edges `ancora_normativa` |
| `decision_unit_type` | payload.tipo_decisorio do registro |
| `normative_text` | payload.texto_dispositivo do object normativo |

### Deduplificação de processos

Hoje ADI 4.277 aparece em N registros (um por dispositivo onde incide). Na migração:

1. Agrupar por `process_key` → **1 object `processo`** por chave única
2. Cada row original → **1 object `registro_jurisprudencial`**
3. Cada registro → **1 edge `ancora_normativa`** (registro → dispositivo)
4. Cada registro → **1 edge `ancora_processual`** (registro → processo)

---

## 8. COMPATIBILIDADE COM CONSTITUIÇÃO ONTOLÓGICA

| Princípio | Verificação |
|---|---|
| 3. Identidade estável (slug) | OK — processos e registros ganham slug próprio |
| 8. Domínios por INSERT | OK — tribunal novo = INSERT em domains + actors |
| 11. Apenas 4 primitivos | OK — tudo é object, actor, event ou edge |
| 13. Temas são objects | OK — não alterado |
| 15. Edge é fonte de verdade | REFORÇADO — ancoragem normativa vira edge |
| 17. source [verbo] target | OK — registro `ancora_normativa` dispositivo |
| 10. Provenance obrigatório | OK — import gera provenance |
| 16. Nunca DELETE | OK — não alterado |

> **Nenhum primitivo alterado (Camada 2).** Apenas adições de types na Camada 1 e novas instâncias na Camada 2.

---

## 9. CHECKLIST DE APROVAÇÃO

- [x] Camada 2 (primitivos) intacta
- [x] Novos types são instâncias legítimas das taxonomias
- [x] Nomenclatura alinhada ao projeto ICONS
- [x] Slug convention globalmente única, sem colisão
- [x] Dupla ancoragem (normativa + processual) opera por edges
- [x] Expansão multi-tribunal funciona sem alteração estrutural
- [x] Migração do icons-db é mapeável 1:1
- [x] Co-ancoragem (1 registro → N dispositivos) é nativa
- [x] Rede jurisprudencial (cita/supera/confirma) é modelável
- [x] Camadas editoriais preservadas como propriedade do edge

---

> **Esta emenda não altera a Constituição Ontológica — estende-a.** Toda adição é INSERT em Camada 1 e instância em Camada 2. O núcleo permanece intacto. A nomenclatura passa a refletir a natureza do projeto.
