-- ============================================================
-- ICONS — Migration 001: Camada 0 — Domínios
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md §4
-- ============================================================

CREATE TABLE domains (
  domain_slug         text PRIMARY KEY,
  label               text NOT NULL,
  parent_domain_slug  text REFERENCES domains (domain_slug),
  valid_from          timestamptz DEFAULT now()
);

CREATE INDEX idx_domains_parent ON domains (parent_domain_slug);

-- Seed: ground zero + estrutura prevista (§4.3–4.4)
INSERT INTO domains (domain_slug, label, parent_domain_slug) VALUES
  ('transversal',  'Entidades transversais',           NULL),
  ('normativo',    'Sistema normativo',                NULL),
  ('juridico',     'Sistema jurídico',                 NULL),
  ('executivo',    'Poder Executivo',                   NULL),
  ('mp',           'Ministério Público',                NULL),
  ('legislativo',  'Poder Legislativo',                 NULL),
  ('controle',     'Órgãos de controle',                NULL);
