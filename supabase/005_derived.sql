-- ============================================================
-- ICONS — Migration 005: Camada 4 — Derivados
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md §20
-- ============================================================

-- ── chunks ──

CREATE TABLE chunks (
  chunk_slug          text PRIMARY KEY,
  object_id           uuid NOT NULL,
  chunk_text          text NOT NULL,
  chunk_index         integer NOT NULL,
  token_estimate      integer,
  hash_chunk          text
);

CREATE INDEX idx_chunks_object ON chunks (object_id);
CREATE INDEX idx_chunks_order ON chunks (object_id, chunk_index);

-- ── embeddings ──

CREATE TABLE embeddings (
  id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  chunk_slug          text NOT NULL REFERENCES chunks (chunk_slug) ON DELETE CASCADE,
  embedding_model     text NOT NULL,
  vector_ref          vector(1536),
  created_at          timestamptz NOT NULL DEFAULT now(),

  UNIQUE (chunk_slug, embedding_model)
);

CREATE INDEX idx_emb_chunk ON embeddings (chunk_slug);
CREATE INDEX idx_emb_model ON embeddings (embedding_model);

-- ── published_objects ──

CREATE TABLE published_objects (
  slug                text PRIMARY KEY,
  payload_json        jsonb NOT NULL,
  payload_hash        text NOT NULL,
  updated_at          timestamptz NOT NULL DEFAULT now()
);
