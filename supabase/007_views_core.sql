-- ============================================================
-- ICONS — Migration 007: Camada 5 — Views Core
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md §21
-- Views estruturais fundamentais (mudam raramente)
-- ============================================================

-- ── objects com domínio e classe resolvidos ──

CREATE OR REPLACE VIEW v_objects_readable AS
SELECT
  o.id,
  o.slug,
  o.type_slug,
  ot.domain_slug,
  ot.ontological_class,
  ot.label AS type_label,
  o.payload,
  o.hash_content,
  o.valid_from,
  o.valid_to,
  o.recorded_at
FROM objects o
JOIN object_types ot ON o.type_slug = ot.type_slug;

-- ── edges com slugs e classe epistêmica resolvidos ──

CREATE OR REPLACE VIEW v_edges_readable AS
SELECT
  e.edge_id,
  e.type_slug,
  et.epistemic_class,
  et.label AS type_label,
  e.source_id,
  src_o.slug AS source_slug,
  e.target_id,
  tgt_o.slug AS target_slug,
  e.weight,
  e.payload,
  e.valid_from,
  e.valid_to,
  e.causation_event_id,
  e.recorded_at
FROM edges e
JOIN edge_types et ON e.type_slug = et.type_slug
LEFT JOIN objects src_o ON e.source_id = src_o.id
LEFT JOIN objects tgt_o ON e.target_id = tgt_o.id;

-- ── estado atual de cada object/actor ──

CREATE OR REPLACE VIEW v_current_state AS
SELECT DISTINCT ON (ev.aggregate_id)
  ev.aggregate_id AS id,
  COALESCE(o.slug, a.slug) AS slug,
  COALESCE(o.type_slug, a.type_slug) AS type_slug,
  COALESCE(ot.domain_slug, at2.domain_slug) AS domain_slug,
  ev.payload->>'to_state' AS current_state,
  ev.occurred_at AS last_event_at
FROM events ev
LEFT JOIN objects o ON ev.aggregate_id = o.id
LEFT JOIN actors a ON ev.aggregate_id = a.id
LEFT JOIN object_types ot ON o.type_slug = ot.type_slug
LEFT JOIN actor_types at2 ON a.type_slug = at2.type_slug
WHERE ev.payload ? 'to_state'
ORDER BY ev.aggregate_id, ev.occurred_at DESC;

-- ── árvore normativa (nós com parent resolvido) ──

CREATE OR REPLACE VIEW v_tree_nodes AS
SELECT
  child.id,
  child.slug,
  child.type_slug,
  ot.domain_slug,
  e.source_id AS parent_id,
  parent.slug AS parent_slug,
  child.payload->>'path_slug' AS path_slug,
  (child.payload->>'depth_level')::int AS depth_level,
  (child.payload->>'sibling_order')::int AS sibling_order
FROM objects child
JOIN object_types ot ON child.type_slug = ot.type_slug
LEFT JOIN edges e ON e.target_id = child.id
  AND e.type_slug = 'parent_of'
  AND e.valid_to IS NULL
LEFT JOIN objects parent ON e.source_id = parent.id
WHERE child.valid_to IS NULL;

-- ── índice de decidibilidade por nó normativo ──

CREATE OR REPLACE VIEW v_decidability_index AS
SELECT
  o.id AS node_id,
  o.slug AS node_slug,
  ot.domain_slug,
  e.type_slug AS edge_type,
  COUNT(*) AS edge_count
FROM objects o
JOIN object_types ot ON o.type_slug = ot.type_slug
JOIN edges e ON e.target_id = o.id AND e.valid_to IS NULL
WHERE ot.domain_slug = 'normativo'
  AND o.valid_to IS NULL
GROUP BY o.id, o.slug, ot.domain_slug, e.type_slug;

-- ── view canônica de ambiente de julgamento (§8.7, §21.2) ──

CREATE OR REPLACE VIEW v_judgment_environment_canonical AS
SELECT
  ev.event_id,
  ev.aggregate_id,
  ev.occurred_at,
  ev.payload->>'decision_body' AS decision_body,
  ev.payload->>'collegiality_mode' AS collegiality_mode,
  ev.payload->>'adjudication_environment' AS adjudication_environment,
  ev.payload->>'session_format' AS session_format,
  (ev.payload->>'oral_argument_present')::boolean AS oral_argument_present,
  ev.payload->>'public_debate_intensity' AS public_debate_intensity,
  (ev.payload->>'panel_size')::int AS panel_size,
  (ev.payload->>'votes_present')::int AS votes_present
FROM events ev
WHERE ev.type_slug = 'julgamento';
