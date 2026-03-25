-- ============================================================
-- ICONS — Migration 008: Camada 5 — Views Analíticas
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md §21
-- Views preditivas, perfis e ecologia (mudam mais frequentemente)
-- ============================================================

-- ── sinais decisórios por caso ──

CREATE OR REPLACE VIEW v_decision_signals AS
SELECT
  jec.aggregate_id AS case_id,
  o.slug AS case_slug,
  ot.domain_slug,
  o.type_slug AS class_code,
  jec.decision_body,
  jec.adjudication_environment,
  jec.collegiality_mode,
  jec.panel_size,
  jec.votes_present,
  jec.oral_argument_present,
  ev.payload->>'outcome' AS outcome,
  ev.payload->>'outcome_polarity' AS outcome_polarity,
  ev.payload->>'decision_direction' AS decision_direction,
  ev.payload->>'decision_unanimity' AS decision_unanimity,
  (ev.payload->>'uses_modulation')::boolean AS uses_modulation,
  ev.payload->>'reasoning_style' AS reasoning_style,
  ev.payload->>'fiscal_effect' AS fiscal_effect,
  ev.payload->>'deference_level' AS deference_level,
  ev.occurred_at AS judgment_date
FROM v_judgment_environment_canonical jec
JOIN events ev ON ev.event_id = jec.event_id
JOIN objects o ON o.id = jec.aggregate_id
JOIN object_types ot ON o.type_slug = ot.type_slug;

-- ── vida processual ──

CREATE OR REPLACE VIEW v_process_lifecycle AS
SELECT
  o.id AS processo_id,
  o.slug AS processo_slug,
  o.type_slug,
  MIN(ev.occurred_at) AS data_nascimento,
  MAX(ev.occurred_at) AS evento_mais_recente,
  MAX(ev.occurred_at) - MIN(ev.occurred_at) AS duracao_total,
  COUNT(ev.event_id) AS numero_eventos
FROM objects o
JOIN object_types ot ON o.type_slug = ot.type_slug
JOIN events ev ON ev.aggregate_id = o.id
WHERE ot.ontological_class = 'processual'
  AND o.valid_to IS NULL
GROUP BY o.id, o.slug, o.type_slug;

-- ── ecologia do julgamento ──

CREATE OR REPLACE VIEW v_judgment_ecology AS
SELECT
  jec.event_id AS julgamento_id,
  jec.aggregate_id AS caso_id,
  o.slug AS caso_slug,
  jec.decision_body,
  jec.adjudication_environment,
  jec.panel_size,
  jec.votes_present,
  ev.payload->>'outcome' AS outcome,
  ev.payload->>'decision_direction' AS direction,
  (ev.payload->>'uses_modulation')::boolean AS uses_modulation,
  ev.payload->>'reasoning_style' AS reasoning_style,
  ev.payload->>'fiscal_effect' AS fiscal_effect,
  ev.occurred_at
FROM v_judgment_environment_canonical jec
JOIN events ev ON ev.event_id = jec.event_id
JOIN objects o ON o.id = jec.aggregate_id
WHERE jec.panel_size IS NOT NULL
  AND jec.votes_present IS NOT NULL;

-- ── perfil decisório por relator ──

CREATE OR REPLACE VIEW v_relator_decision_profile AS
SELECT
  a.id AS actor_id,
  a.slug AS actor_slug,
  COUNT(*) AS total_decisions,
  COUNT(*) FILTER (WHERE ds.outcome = 'procedente') AS procedente_count,
  COUNT(*) FILTER (WHERE ds.uses_modulation = true) AS modulacao_count,
  COUNT(*) FILTER (WHERE ds.fiscal_effect = 'contencao') AS contencao_count,
  ROUND(COUNT(*) FILTER (WHERE ds.outcome = 'procedente')::numeric / NULLIF(COUNT(*), 0), 3) AS procedencia_rate,
  ROUND(COUNT(*) FILTER (WHERE ds.uses_modulation = true)::numeric / NULLIF(COUNT(*), 0), 3) AS modulacao_rate,
  ROUND(COUNT(*) FILTER (WHERE ds.fiscal_effect = 'contencao')::numeric / NULLIF(COUNT(*), 0), 3) AS contencao_fiscal_rate,
  MODE() WITHIN GROUP (ORDER BY ds.reasoning_style) AS dominant_reasoning_style
FROM actors a
JOIN edges e ON e.source_id = a.id
  AND e.type_slug = 'relator_de'
  AND e.valid_to IS NULL
JOIN v_decision_signals ds ON ds.case_id = e.target_id
WHERE a.type_slug = 'ministro_stf'
GROUP BY a.id, a.slug;

-- ── perfil por relator × ambiente ──

CREATE OR REPLACE VIEW v_relator_environment_profile AS
SELECT
  a.id AS actor_id,
  a.slug AS actor_slug,
  ds.adjudication_environment AS environment,
  COUNT(*) AS total_decisions,
  ROUND(COUNT(*) FILTER (WHERE ds.outcome = 'procedente')::numeric / NULLIF(COUNT(*), 0), 3) AS procedencia_rate_env,
  ROUND(COUNT(*) FILTER (WHERE ds.uses_modulation = true)::numeric / NULLIF(COUNT(*), 0), 3) AS modulacao_rate_env,
  ROUND(COUNT(*) FILTER (WHERE ds.fiscal_effect = 'contencao')::numeric / NULLIF(COUNT(*), 0), 3) AS contencao_rate_env
FROM actors a
JOIN edges e ON e.source_id = a.id
  AND e.type_slug = 'relator_de'
  AND e.valid_to IS NULL
JOIN v_decision_signals ds ON ds.case_id = e.target_id
WHERE a.type_slug = 'ministro_stf'
  AND ds.adjudication_environment IS NOT NULL
GROUP BY a.id, a.slug, ds.adjudication_environment;

-- ── perfil por órgão decisório ──

CREATE OR REPLACE VIEW v_body_decision_profile AS
SELECT
  ds.decision_body,
  COUNT(*) AS total_decisions,
  ROUND(COUNT(*) FILTER (WHERE ds.outcome = 'procedente')::numeric / NULLIF(COUNT(*), 0), 3) AS procedencia_rate,
  ROUND(COUNT(*) FILTER (WHERE ds.uses_modulation = true)::numeric / NULLIF(COUNT(*), 0), 3) AS modulacao_rate,
  ROUND(COUNT(*) FILTER (WHERE ds.fiscal_effect = 'contencao')::numeric / NULLIF(COUNT(*), 0), 3) AS contencao_rate,
  MODE() WITHIN GROUP (ORDER BY ds.reasoning_style) AS dominant_reasoning_style
FROM v_decision_signals ds
WHERE ds.decision_body IS NOT NULL
GROUP BY ds.decision_body;

-- ── perfil órgão × ambiente ──

CREATE OR REPLACE VIEW v_body_environment_profile AS
SELECT
  ds.decision_body,
  ds.adjudication_environment AS environment,
  COUNT(*) AS total_decisions,
  ROUND(COUNT(*) FILTER (WHERE ds.outcome = 'procedente')::numeric / NULLIF(COUNT(*), 0), 3) AS procedencia_rate,
  ROUND(COUNT(*) FILTER (WHERE ds.uses_modulation = true)::numeric / NULLIF(COUNT(*), 0), 3) AS modulacao_rate
FROM v_decision_signals ds
WHERE ds.decision_body IS NOT NULL
  AND ds.adjudication_environment IS NOT NULL
GROUP BY ds.decision_body, ds.adjudication_environment;

-- ── perfil relator × órgão ──

CREATE OR REPLACE VIEW v_relator_orgao_decision_profile AS
SELECT
  a.slug AS actor_slug,
  ds.decision_body,
  COUNT(*) AS total_decisions,
  ROUND(COUNT(*) FILTER (WHERE ds.outcome = 'procedente')::numeric / NULLIF(COUNT(*), 0), 3) AS procedencia_rate,
  ROUND(COUNT(*) FILTER (WHERE ds.uses_modulation = true)::numeric / NULLIF(COUNT(*), 0), 3) AS modulacao_rate
FROM actors a
JOIN edges e ON e.source_id = a.id
  AND e.type_slug = 'relator_de'
  AND e.valid_to IS NULL
JOIN v_decision_signals ds ON ds.case_id = e.target_id
WHERE a.type_slug = 'ministro_stf'
  AND ds.decision_body IS NOT NULL
GROUP BY a.slug, ds.decision_body;

-- ── perfil por subject × ambiente ──

CREATE OR REPLACE VIEW v_subject_environment_profile AS
SELECT
  subj.slug AS subject_slug,
  ds.adjudication_environment AS environment,
  COUNT(*) AS total_decisions,
  ROUND(COUNT(*) FILTER (WHERE ds.outcome = 'procedente')::numeric / NULLIF(COUNT(*), 0), 3) AS procedencia_rate,
  MODE() WITHIN GROUP (ORDER BY ds.decision_direction) AS dominant_direction
FROM objects subj
JOIN edges e_sobre ON e_sobre.target_id = subj.id
  AND e_sobre.type_slug = 'sobre'
  AND e_sobre.valid_to IS NULL
JOIN v_decision_signals ds ON ds.case_id = e_sobre.source_id
WHERE subj.type_slug = 'subject'
  AND ds.adjudication_environment IS NOT NULL
GROUP BY subj.slug, ds.adjudication_environment;

-- ── features preditivas (pronto para ML) ──

CREATE OR REPLACE VIEW v_predictive_features AS
SELECT
  ds.case_id,
  ds.case_slug,
  ds.class_code,
  ds.decision_body,
  ds.adjudication_environment,
  ds.panel_size,
  ds.votes_present,
  ds.judgment_date,
  ds.outcome AS outcome_label,
  ds.decision_direction AS direction_label,
  ds.uses_modulation AS modulation_label,
  ds.fiscal_effect AS fiscal_effect_label,
  ds.reasoning_style,
  ds.deference_level
FROM v_decision_signals ds;
