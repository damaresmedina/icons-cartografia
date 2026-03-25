-- ============================================================
-- ICONS — Migration 003: Camada 2 — Primitivos Universais
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md §6
-- Organização: tabelas → constraints → funções → triggers → seed
-- ============================================================

-- ════════════════════════════════════════
-- TABELAS
-- ════════════════════════════════════════

-- ── 6.1 objects ──

CREATE TABLE objects (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug            text UNIQUE NOT NULL,
  type_slug       text NOT NULL REFERENCES object_types (type_slug),
  payload         jsonb,
  hash_content    text,
  valid_from      timestamptz,
  valid_to        timestamptz,
  recorded_at     timestamptz NOT NULL DEFAULT now()
);

-- ── 6.2 actors ──

CREATE TABLE actors (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug            text UNIQUE NOT NULL,
  type_slug       text NOT NULL REFERENCES actor_types (type_slug),
  payload         jsonb,
  dedup_hash      text,
  valid_from      timestamptz,
  valid_to        timestamptz,
  recorded_at     timestamptz NOT NULL DEFAULT now()
);

-- ── 6.3 events (append-only, imutável) ──

CREATE TABLE events (
  event_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type_slug       text NOT NULL REFERENCES event_types (type_slug),
  aggregate_id    uuid NOT NULL,
  actor_id        uuid NOT NULL REFERENCES actors (id),
  payload         jsonb,
  causation_id    uuid REFERENCES events (event_id),
  occurred_at     timestamptz NOT NULL,
  recorded_at     timestamptz NOT NULL DEFAULT now()
);

-- ── 6.4 edges ──

CREATE TABLE edges (
  edge_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type_slug            text NOT NULL REFERENCES edge_types (type_slug),
  source_id            uuid NOT NULL,
  target_id            uuid NOT NULL,
  weight               float,
  payload              jsonb,
  valid_from           timestamptz,
  valid_to             timestamptz,
  causation_event_id   uuid REFERENCES events (event_id),
  recorded_at          timestamptz NOT NULL DEFAULT now()
);

-- ════════════════════════════════════════
-- ÍNDICES (§25)
-- ════════════════════════════════════════

-- objects
CREATE INDEX idx_obj_type ON objects (type_slug);
CREATE INDEX idx_obj_slug ON objects (slug);
CREATE INDEX idx_obj_valid_from ON objects (valid_from);
CREATE INDEX idx_obj_valid_to ON objects (valid_to);

-- actors
CREATE INDEX idx_act_type ON actors (type_slug);
CREATE INDEX idx_act_slug ON actors (slug);
CREATE INDEX idx_act_valid_from ON actors (valid_from);

-- events
CREATE INDEX idx_evt_aggregate ON events (aggregate_id, occurred_at);
CREATE INDEX idx_evt_type ON events (type_slug);
CREATE INDEX idx_evt_actor ON events (actor_id);
CREATE INDEX idx_evt_payload ON events USING GIN (payload);

-- edges
CREATE INDEX idx_edg_type_source ON edges (type_slug, source_id);
CREATE INDEX idx_edg_type_target ON edges (type_slug, target_id);
CREATE INDEX idx_edg_source ON edges (source_id);
CREATE INDEX idx_edg_target ON edges (target_id);
CREATE INDEX idx_edg_payload ON edges USING GIN (payload);

-- ════════════════════════════════════════
-- FUNÇÕES AUXILIARES
-- ════════════════════════════════════════

-- Unicidade global de slugs entre objects e actors (§6.5, princípio 14)
CREATE OR REPLACE FUNCTION check_slug_global_uniqueness()
RETURNS trigger AS $$
BEGIN
  IF TG_TABLE_NAME = 'objects' THEN
    IF EXISTS (SELECT 1 FROM actors WHERE slug = NEW.slug) THEN
      RAISE EXCEPTION 'Slug "%" já existe em actors. Slugs devem ser globalmente únicos.', NEW.slug;
    END IF;
  ELSIF TG_TABLE_NAME = 'actors' THEN
    IF EXISTS (SELECT 1 FROM objects WHERE slug = NEW.slug) THEN
      RAISE EXCEPTION 'Slug "%" já existe em objects. Slugs devem ser globalmente únicos.', NEW.slug;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Enforcement de allows_multiple = false (§5.4)
CREATE OR REPLACE FUNCTION check_edge_allows_multiple()
RETURNS trigger AS $$
DECLARE
  v_allows boolean;
BEGIN
  SELECT allows_multiple INTO v_allows
  FROM edge_types WHERE type_slug = NEW.type_slug;

  IF v_allows = false THEN
    IF EXISTS (
      SELECT 1 FROM edges
      WHERE type_slug = NEW.type_slug
        AND source_id = NEW.source_id
        AND target_id = NEW.target_id
        AND valid_to IS NULL
        AND edge_id != COALESCE(NEW.edge_id, '00000000-0000-0000-0000-000000000000'::uuid)
    ) THEN
      RAISE EXCEPTION 'Edge type "%" não permite múltiplos edges ativos entre o mesmo par source/target.', NEW.type_slug;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Enforcement de weight_required (§5.4)
CREATE OR REPLACE FUNCTION check_edge_weight_required()
RETURNS trigger AS $$
DECLARE
  v_required boolean;
BEGIN
  SELECT weight_required INTO v_required
  FROM edge_types WHERE type_slug = NEW.type_slug;

  IF v_required = true AND NEW.weight IS NULL THEN
    RAISE EXCEPTION 'Edge type "%" exige weight obrigatório.', NEW.type_slug;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Proteção contra DELETE (princípio 16)
CREATE OR REPLACE FUNCTION prevent_delete()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'DELETE não é permitido na tabela %. Use valid_to para encerrar.', TG_TABLE_NAME;
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Proteção contra UPDATE em events (§6.3: append-only, imutável)
CREATE OR REPLACE FUNCTION prevent_event_update()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'Events são imutáveis. Nunca UPDATE, nunca DELETE.';
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- ════════════════════════════════════════
-- TRIGGERS
-- ════════════════════════════════════════

-- Unicidade global de slugs
CREATE TRIGGER trg_objects_slug_unique
  BEFORE INSERT OR UPDATE OF slug ON objects
  FOR EACH ROW EXECUTE FUNCTION check_slug_global_uniqueness();

CREATE TRIGGER trg_actors_slug_unique
  BEFORE INSERT OR UPDATE OF slug ON actors
  FOR EACH ROW EXECUTE FUNCTION check_slug_global_uniqueness();

-- Edge allows_multiple
CREATE TRIGGER trg_edge_allows_multiple
  BEFORE INSERT ON edges
  FOR EACH ROW EXECUTE FUNCTION check_edge_allows_multiple();

-- Edge weight_required
CREATE TRIGGER trg_edge_weight_required
  BEFORE INSERT ON edges
  FOR EACH ROW EXECUTE FUNCTION check_edge_weight_required();

-- Prevent DELETE em primitivos
CREATE TRIGGER trg_objects_no_delete
  BEFORE DELETE ON objects
  FOR EACH ROW EXECUTE FUNCTION prevent_delete();

CREATE TRIGGER trg_actors_no_delete
  BEFORE DELETE ON actors
  FOR EACH ROW EXECUTE FUNCTION prevent_delete();

CREATE TRIGGER trg_edges_no_delete
  BEFORE DELETE ON edges
  FOR EACH ROW EXECUTE FUNCTION prevent_delete();

-- Events: imutáveis
CREATE TRIGGER trg_events_no_update
  BEFORE UPDATE ON events
  FOR EACH ROW EXECUTE FUNCTION prevent_event_update();

CREATE TRIGGER trg_events_no_delete
  BEFORE DELETE ON events
  FOR EACH ROW EXECUTE FUNCTION prevent_delete();

-- ════════════════════════════════════════
-- SEED: actor sistema-pipeline (§5.2, §6.3)
-- ════════════════════════════════════════

INSERT INTO actors (slug, type_slug, payload, valid_from)
VALUES ('sistema-pipeline', 'sistema', '{"description": "Ator automatizado do pipeline de ingestão"}', now());
