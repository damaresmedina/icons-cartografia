# PROTOCOLO ONTOLÓGICO UNIVERSAL

## Cartografia Massiva da Litigância do Estado Brasileiro

---

# 1. ÂNCORA E FINALIDADE

**Autora:** Damares Medina
**Objeto:** Cartografia massiva da litigância do Estado brasileiro
**Princípio:** O sistema modela **relações entre estruturas normativas e documentos jurídicos**, não apenas textos isolados.

---

# 2. PRINCÍPIOS INEGOCIÁVEIS

1. Todo corpus jurídico é uma **árvore multinível**
2. O artigo **não é a raiz** da estrutura normativa
3. Todo objeto possui **identidade estável (slug)**
4. Estrutura ≠ texto ≠ derivação
5. Embeddings são **derivados, nunca estruturais**
6. A base é **corpus-agnóstica e hierarquia-aware**
7. Nenhuma camada depende do frontend

---

# 3. ONTOLOGIA UNIVERSAL

O sistema se organiza em 9 entidades fundamentais:

| Entidade       | Função                  |
| -------------- | ----------------------- |
| `work`         | obra jurídica           |
| `version`      | versão textual          |
| `node`         | unidade estrutural      |
| `document`     | objeto documental       |
| `annotation`   | anotação editorial      |
| `citation`     | vínculo explícito       |
| `relationship` | relação estrutural      |
| `chunk`        | unidade textual         |
| `embedding`    | representação semântica |

---

# 4. CAMADAS DO SISTEMA

## 4.1 RAW

Fonte original:

* HTML
* XML
* PDF
* texto bruto

## 4.2 NORMALIZED

Estrutura canônica:

* nós
* textos limpos
* slugs
* relações

## 4.3 DERIVED

Derivados:

* JSON
* chunks
* embeddings
* índices
* agregações

---

# 5. ESTRUTURA FUNDAMENTAL

## 5.1 `works`

Define a obra.

Campos:

* `work_slug`
* `title`
* `jurisdiction`
* `work_type`
* `source_url`
* `source_hash`

---

## 5.2 `work_versions`

Define versões.

Campos:

* `version_slug`
* `work_slug`
* `valid_from`
* `valid_to`
* `source_hash`

---

# 6. ÁRVORE UNIVERSAL (`legal_nodes`)

## 6.1 Definição

Cada nó representa qualquer unidade estrutural.

## 6.2 Tipos possíveis

* livro
* parte
* título
* capítulo
* seção
* subseção
* artigo
* caput
* parágrafo
* inciso
* alínea
* item
* anexo

---

## 6.3 Campos obrigatórios

* `node_slug`
* `node_type`
* `work_slug`
* `version_slug`
* `text_content`
* `normalized_text`

### Estrutura:

* `parent_node_slug`
* `container_node_slug`
* `macro_container_slug`
* `root_node_slug`
* `path_slug`
* `depth_level`
* `sibling_order`

### Controle:

* `hash_content`
* `is_leaf`
* `is_repealed`

---

## 6.4 Regra estrutural

> Nenhum nó pode existir sem saber sua posição na árvore.

---

# 7. CONVENÇÃO DE SLUG

## 7.1 Princípios

* determinística
* estável
* legível
* independente de contexto

---

## 7.2 Formato base

### obra

`cf-1988`

### versão

`cf-1988-2026`

### artigo

`cf-1988-art-5`

### caput

`cf-1988-art-5-caput`

### inciso

`cf-1988-art-5-inc-ix`

### alínea

`cf-1988-art-5-inc-ix-ali-a`

### parágrafo

`cf-1988-art-5-par-1`

---

## 7.3 Caminho completo

```text
cf-1988/titulo-2/capitulo-1/art-5/inc-ix
```

---

## 7.4 Regra essencial

> Slug identifica o objeto.
> Path identifica a posição.

---

# 8. DOCUMENTOS (`documents`)

Campos:

* `document_slug`
* `document_type`
* `process_number`
* `court`
* `class_code`
* `rapporteur`
* `judgment_date`
* `full_text`
* `summary_text`
* `source_url`
* `hash_content`

---

# 9. ANOTAÇÕES (`annotations`)

Campos:

* `annotation_slug`
* `target_node_slug`
* `annotation_text`
* `normalized_text`
* `source_url`
* `hash_content`

---

## Regra

> Sempre vincular ao menor nó possível.

---

# 10. CITAÇÕES (`citations`)

Campos:

* `source_object_slug`
* `target_object_slug`
* `citation_text_raw`
* `citation_kind`
* `confidence_score`

Tipos:

* interpreta
* cita
* aplica
* remete
* revoga

---

# 11. RELAÇÕES (`node_relationships`)

Campos:

* `source_node_slug`
* `target_node_slug`
* `relationship_type`

Tipos:

* parent_of
* refers_to
* amends
* revokes

---

# 12. SEGMENTAÇÃO (`chunks`)

Campos:

* `chunk_slug`
* `object_slug`
* `chunk_text`
* `chunk_index`
* `token_estimate`
* `hash_chunk`

---

# 13. EMBEDDINGS (`embeddings`)

Campos:

* `chunk_slug`
* `embedding_model`
* `vector_ref`
* `created_at`

---

## Regra central

> Embedding nunca substitui estrutura.

---

# 14. IDENTIDADE MULTINÍVEL

| nível      | função        |
| ---------- | ------------- |
| slug       | identidade    |
| hash       | versão        |
| chunk_slug | granularidade |
| path       | localização   |

---

# 15. REGRAS DE VÍNCULO

1. Vincular ao nó mais específico
2. Nunca colapsar no caput
3. Subir por agregação
4. Registrar incerteza
5. Separar vínculo inferido de vínculo confirmado

---

# 16. ESCALABILIDADE

## Chaves estruturais

* `work_slug`
* `version_slug`
* `node_type`
* `jurisdiction`
* `year`

---

## Estratégia

* rebuild parcial por work
* reindexação por hash
* chunking incremental
* embeddings sob demanda

---

# 17. BUSCA

## 17.1 Lexical

* palavra exata
* filtros

## 17.2 Semântica

* similaridade
* embeddings

## 17.3 Híbrida

* filtro + ranking semântico

---

# 18. SERVING

## `published_objects`

Campos:

* `slug`
* `payload_json`
* `payload_hash`

---

## Regra

> JSON nunca é base primária.

---

# 19. PIPELINE

1. ingestão
2. canonização
3. parsing
4. vinculação
5. normalização
6. chunking
7. embeddings
8. indexação
9. publicação

---

# 20. ERROS PROIBIDOS

* colapsar estrutura
* modelar por tela
* usar slug como única estrutura
* misturar camadas
* embeddar antes de estruturar
* perder vínculo com fonte

---

# 21. FÓRMULA FINAL

```text
WORK
→ VERSION
→ LEGAL NODES (ÁRVORE COMPLETA)
→ ANNOTATIONS
→ DOCUMENTS
→ CITATIONS
→ CHUNKS
→ EMBEDDINGS
→ JSON / API / VIEWS
```

---

# 22. PRINCÍPIO FINAL

> O sistema não organiza textos.
> Ele organiza relações estruturadas entre textos, decisões e normas, em múltiplas escalas.

---

**Este protocolo define a arquitetura permanente do sistema.
Nenhuma implementação deve violar suas regras estruturais.**
