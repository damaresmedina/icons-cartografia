-- ============================================================
-- ICONS - Cartografia Massiva da Litigância do Estado Brasileiro
-- Schema v1.0 - Protocolo Ontológico Universal
-- ============================================================

-- Extensões
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE node_type_enum AS ENUM (
  'livro', 'parte', 'titulo', 'capitulo', 'secao', 'subsecao',
  'artigo', 'caput', 'paragrafo', 'inciso', 'alinea', 'item', 'anexo'
);

CREATE TYPE citation_kind_enum AS ENUM (
  'interpreta', 'cita', 'aplica', 'remete', 'revoga'
);

CREATE TYPE relationship_type_enum AS ENUM (
  'parent_of', 'refers_to', 'amends', 'revokes'
);

-- ============================================================
-- 1. WORKS (obra jurídica)
-- ============================================================

CREATE TABLE works (
  work_slug    TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  jurisdiction TEXT NOT NULL,
  work_type    TEXT NOT NULL,
  source_url   TEXT,
  source_hash  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_works_jurisdiction ON works (jurisdiction);
CREATE INDEX idx_works_type ON works (work_type);

-- ============================================================
-- 2. WORK_VERSIONS (versão textual)
-- ============================================================

CREATE TABLE work_versions (
  version_slug TEXT PRIMARY KEY,
  work_slug    TEXT NOT NULL REFERENCES works (work_slug) ON DELETE CASCADE,
  valid_from   DATE,
  valid_to     DATE,
  source_hash  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_versions_work ON work_versions (work_slug);

-- ============================================================
-- 3. LEGAL_NODES (árvore universal)
-- ============================================================

CREATE TABLE legal_nodes (
  node_slug           TEXT PRIMARY KEY,
  node_type           node_type_enum NOT NULL,
  work_slug           TEXT NOT NULL REFERENCES works (work_slug) ON DELETE CASCADE,
  version_slug        TEXT NOT NULL REFERENCES work_versions (version_slug) ON DELETE CASCADE,

  -- conteúdo
  text_content        TEXT,
  normalized_text     TEXT,

  -- estrutura hierárquica
  parent_node_slug    TEXT REFERENCES legal_nodes (node_slug),
  container_node_slug TEXT REFERENCES legal_nodes (node_slug),
  macro_container_slug TEXT REFERENCES legal_nodes (node_slug),
  root_node_slug      TEXT REFERENCES legal_nodes (node_slug),
  path_slug           TEXT NOT NULL,
  depth_level         INTEGER NOT NULL,
  sibling_order       INTEGER NOT NULL,

  -- controle
  hash_content        TEXT,
  is_leaf             BOOLEAN NOT NULL DEFAULT true,
  is_repealed         BOOLEAN NOT NULL DEFAULT false,

  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_nodes_work ON legal_nodes (work_slug);
CREATE INDEX idx_nodes_version ON legal_nodes (version_slug);
CREATE INDEX idx_nodes_parent ON legal_nodes (parent_node_slug);
CREATE INDEX idx_nodes_type ON legal_nodes (node_type);
CREATE INDEX idx_nodes_path ON legal_nodes (path_slug);
CREATE INDEX idx_nodes_depth ON legal_nodes (depth_level);
CREATE INDEX idx_nodes_container ON legal_nodes (container_node_slug);
CREATE INDEX idx_nodes_root ON legal_nodes (root_node_slug);

-- ============================================================
-- 4. DOCUMENTS (objeto documental)
-- ============================================================

CREATE TABLE documents (
  document_slug  TEXT PRIMARY KEY,
  document_type  TEXT NOT NULL,
  process_number TEXT,
  court          TEXT,
  class_code     TEXT,
  rapporteur     TEXT,
  judgment_date  DATE,
  full_text      TEXT,
  summary_text   TEXT,
  source_url     TEXT,
  hash_content   TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_docs_type ON documents (document_type);
CREATE INDEX idx_docs_court ON documents (court);
CREATE INDEX idx_docs_rapporteur ON documents (rapporteur);
CREATE INDEX idx_docs_judgment ON documents (judgment_date);
CREATE INDEX idx_docs_class ON documents (class_code);
CREATE INDEX idx_docs_process ON documents (process_number);

-- ============================================================
-- 5. ANNOTATIONS (anotação editorial)
-- ============================================================

CREATE TABLE annotations (
  annotation_slug  TEXT PRIMARY KEY,
  target_node_slug TEXT NOT NULL REFERENCES legal_nodes (node_slug) ON DELETE CASCADE,
  annotation_text  TEXT NOT NULL,
  normalized_text  TEXT,
  source_url       TEXT,
  hash_content     TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_annotations_target ON annotations (target_node_slug);

-- ============================================================
-- 6. CITATIONS (vínculo explícito)
-- ============================================================

CREATE TABLE citations (
  id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_object_slug  TEXT NOT NULL,
  target_object_slug  TEXT NOT NULL,
  citation_text_raw   TEXT,
  citation_kind       citation_kind_enum NOT NULL,
  confidence_score    REAL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_citations_source ON citations (source_object_slug);
CREATE INDEX idx_citations_target ON citations (target_object_slug);
CREATE INDEX idx_citations_kind ON citations (citation_kind);

-- ============================================================
-- 7. NODE_RELATIONSHIPS (relação estrutural)
-- ============================================================

CREATE TABLE node_relationships (
  id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_node_slug   TEXT NOT NULL,
  target_node_slug   TEXT NOT NULL,
  relationship_type  relationship_type_enum NOT NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (source_node_slug, target_node_slug, relationship_type)
);

CREATE INDEX idx_rels_source ON node_relationships (source_node_slug);
CREATE INDEX idx_rels_target ON node_relationships (target_node_slug);
CREATE INDEX idx_rels_type ON node_relationships (relationship_type);

-- ============================================================
-- 8. CHUNKS (unidade textual segmentada)
-- ============================================================

CREATE TABLE chunks (
  chunk_slug     TEXT PRIMARY KEY,
  object_slug    TEXT NOT NULL,
  chunk_text     TEXT NOT NULL,
  chunk_index    INTEGER NOT NULL,
  token_estimate INTEGER,
  hash_chunk     TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_object ON chunks (object_slug);
CREATE INDEX idx_chunks_order ON chunks (object_slug, chunk_index);

-- ============================================================
-- 9. EMBEDDINGS (representação semântica)
-- ============================================================

CREATE TABLE embeddings (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  chunk_slug      TEXT NOT NULL REFERENCES chunks (chunk_slug) ON DELETE CASCADE,
  embedding_model TEXT NOT NULL,
  vector_ref      vector(1536),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (chunk_slug, embedding_model)
);

CREATE INDEX idx_embeddings_chunk ON embeddings (chunk_slug);
CREATE INDEX idx_embeddings_model ON embeddings (embedding_model);

-- ============================================================
-- 10. PUBLISHED_OBJECTS (serving layer)
-- ============================================================

CREATE TABLE published_objects (
  slug          TEXT PRIMARY KEY,
  payload_json  JSONB NOT NULL,
  payload_hash  TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- RLS (Row Level Security)
-- ============================================================

ALTER TABLE works ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE citations ENABLE ROW LEVEL SECURITY;
ALTER TABLE node_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE published_objects ENABLE ROW LEVEL SECURITY;

-- Leitura pública para todas as tabelas
CREATE POLICY "public_read" ON works FOR SELECT USING (true);
CREATE POLICY "public_read" ON work_versions FOR SELECT USING (true);
CREATE POLICY "public_read" ON legal_nodes FOR SELECT USING (true);
CREATE POLICY "public_read" ON documents FOR SELECT USING (true);
CREATE POLICY "public_read" ON annotations FOR SELECT USING (true);
CREATE POLICY "public_read" ON citations FOR SELECT USING (true);
CREATE POLICY "public_read" ON node_relationships FOR SELECT USING (true);
CREATE POLICY "public_read" ON chunks FOR SELECT USING (true);
CREATE POLICY "public_read" ON embeddings FOR SELECT USING (true);
CREATE POLICY "public_read" ON published_objects FOR SELECT USING (true);

-- Escrita via service_role apenas
CREATE POLICY "service_write" ON works FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON work_versions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON legal_nodes FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON documents FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON annotations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON citations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON node_relationships FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON chunks FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON embeddings FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON published_objects FOR ALL USING (auth.role() = 'service_role');
