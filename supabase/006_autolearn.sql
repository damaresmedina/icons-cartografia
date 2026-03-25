-- ============================================================
-- ICONS — Migration 006: Sistema Autoensinável + Membrana
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md §10
-- ============================================================

-- ── Perfis decisórios aprendidos (§10.5) ──

CREATE TABLE learned_decision_profiles (
  profile_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_type        text NOT NULL,
  target_slug         text NOT NULL,
  period_start        date,
  period_end          date,
  sample_size         integer,
  profile_payload     jsonb,
  confidence_score    float,
  stability_score     float,
  predictive_gain     float,
  status              text NOT NULL DEFAULT 'proposed',
  created_at          timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT chk_profile_type CHECK (
    profile_type IN ('relator', 'orgao', 'relator_orgao', 'relator_environment', 'orgao_environment')
  ),
  CONSTRAINT chk_profile_status CHECK (
    status IN ('proposed', 'validated', 'incorporated', 'rejected', 'superseded')
  )
);

CREATE INDEX idx_ldp_type ON learned_decision_profiles (profile_type);
CREATE INDEX idx_ldp_target ON learned_decision_profiles (target_slug);
CREATE INDEX idx_ldp_status ON learned_decision_profiles (status);

-- ── Propostas ontológicas / membrana (§10.6) ──

CREATE TABLE ontology_proposals (
  proposal_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_type       text NOT NULL,
  description         text,
  evidence_payload    jsonb,
  recurrence_count    integer,
  stability_score     float,
  predictive_gain     float,
  compatibility_score float,
  status              text NOT NULL DEFAULT 'pending',
  created_at          timestamptz NOT NULL DEFAULT now(),
  reviewed_at         timestamptz,

  CONSTRAINT chk_proposal_type CHECK (
    proposal_type IN (
      'new_decision_pattern', 'new_reasoning_pattern', 'new_fiscal_pattern',
      'new_predictive_feature', 'new_body_pattern', 'new_relator_pattern',
      'new_environment_pattern'
    )
  ),
  CONSTRAINT chk_proposal_status CHECK (
    status IN ('pending', 'validated', 'incorporated', 'rejected')
  )
);

CREATE INDEX idx_op_type ON ontology_proposals (proposal_type);
CREATE INDEX idx_op_status ON ontology_proposals (status);
