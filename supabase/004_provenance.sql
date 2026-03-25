-- ============================================================
-- ICONS — Migration 004: Camada 3 — Provenance
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md §19
-- ============================================================

CREATE TABLE provenance (
  provenance_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  target_id           uuid NOT NULL,
  target_table        text NOT NULL,
  source_type         text NOT NULL,
  source_url          text,
  pipeline_version    text,
  confidence          float,
  hash_input          text,
  hash_output         text,
  produced_at         timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT chk_target_table CHECK (
    target_table IN ('objects', 'actors', 'events', 'edges')
  ),
  CONSTRAINT chk_source_type CHECK (
    source_type IN ('manual', 'scraping', 'parsing', 'pipeline', 'ia')
  )
);

CREATE INDEX idx_prov_target ON provenance (target_id, target_table);
CREATE INDEX idx_prov_source ON provenance (source_type);
CREATE INDEX idx_prov_produced ON provenance (produced_at);
