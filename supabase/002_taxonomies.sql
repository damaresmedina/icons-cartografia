-- ============================================================
-- ICONS — Migration 002: Camada 1 — Taxonomias Vivas
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md §5
-- ============================================================

-- ── 5.1 object_types ──

CREATE TABLE object_types (
  type_slug           text PRIMARY KEY,
  domain_slug         text REFERENCES domains (domain_slug),
  ontological_class   text NOT NULL,
  label               text NOT NULL,
  valid_from          timestamptz DEFAULT now()
);

CREATE INDEX idx_ot_domain ON object_types (domain_slug);
CREATE INDEX idx_ot_class ON object_types (ontological_class);

-- ── 5.2 actor_types ──

CREATE TABLE actor_types (
  type_slug           text PRIMARY KEY,
  domain_slug         text REFERENCES domains (domain_slug),
  actor_class         text NOT NULL,
  label               text NOT NULL,
  valid_from          timestamptz DEFAULT now()
);

CREATE INDEX idx_at_domain ON actor_types (domain_slug);
CREATE INDEX idx_at_class ON actor_types (actor_class);

-- ── 5.3 event_types ──

CREATE TABLE event_types (
  type_slug           text PRIMARY KEY,
  domain_slug         text REFERENCES domains (domain_slug),
  event_class         text NOT NULL,
  label               text NOT NULL,
  valid_from          timestamptz DEFAULT now()
);

CREATE INDEX idx_et_domain ON event_types (domain_slug);
CREATE INDEX idx_et_class ON event_types (event_class);

-- ── 5.4 edge_types ──

CREATE TABLE edge_types (
  type_slug           text PRIMARY KEY,
  source_domain_slug  text REFERENCES domains (domain_slug),
  target_domain_slug  text REFERENCES domains (domain_slug),
  epistemic_class     text NOT NULL,
  label               text NOT NULL,
  bidirectional       boolean NOT NULL DEFAULT false,
  allows_multiple     boolean NOT NULL DEFAULT true,
  weight_semantics    text,
  weight_required     boolean NOT NULL DEFAULT false,
  valid_from          timestamptz DEFAULT now()
);

CREATE INDEX idx_edt_source ON edge_types (source_domain_slug);
CREATE INDEX idx_edt_target ON edge_types (target_domain_slug);
CREATE INDEX idx_edt_epistemic ON edge_types (epistemic_class);

-- ── 5.5 state_types ──

CREATE TABLE state_types (
  type_slug           text NOT NULL,
  object_type_slug    text NOT NULL REFERENCES object_types (type_slug),
  domain_slug         text NOT NULL REFERENCES domains (domain_slug),
  label               text NOT NULL,
  terminal            boolean NOT NULL DEFAULT false,
  valid_from          timestamptz DEFAULT now(),
  PRIMARY KEY (type_slug, object_type_slug)
);

CREATE INDEX idx_st_domain ON state_types (domain_slug);
CREATE INDEX idx_st_object ON state_types (object_type_slug);

-- ============================================================
-- SEED: todos os types do ground zero
-- ============================================================

-- object_types (26)
INSERT INTO object_types (type_slug, domain_slug, ontological_class, label) VALUES
  ('constituicao',             'normativo',    'estrutural',    'Constituição'),
  ('versao_normativa',         'normativo',    'estrutural',    'Versão/marco temporal de obra normativa'),
  ('emenda_constitucional',    'normativo',    'estrutural',    'Emenda Constitucional'),
  ('titulo',                   'normativo',    'estrutural',    'Título'),
  ('capitulo',                 'normativo',    'estrutural',    'Capítulo'),
  ('secao',                    'normativo',    'estrutural',    'Seção'),
  ('artigo',                   'normativo',    'estrutural',    'Artigo'),
  ('caput',                    'normativo',    'estrutural',    'Caput'),
  ('inciso',                   'normativo',    'estrutural',    'Inciso'),
  ('paragrafo',                'normativo',    'estrutural',    'Parágrafo'),
  ('alinea',                   'normativo',    'estrutural',    'Alínea'),
  ('acao_direta',              'juridico',     'processual',    'Ação Direta'),
  ('recurso_extraordinario',   'juridico',     'processual',    'Recurso Extraordinário'),
  ('sumula_vinculante',        'juridico',     'estrutural',    'Súmula Vinculante'),
  ('decreto',                  'executivo',    'estrutural',    'Decreto'),
  ('projeto_lei',              'legislativo',  'processual',    'Projeto de Lei'),
  ('subject',                  'transversal',  'semantico',     'Tema/assunto'),
  ('anotacao',                 'transversal',  'editorial',     'Anotação editorial'),
  ('argumento',                'juridico',     'argumentativo', 'Razão de decidir / fundamento'),
  ('impacto_orcamentario',     'transversal',  'analitico',     'Impacto orçamentário de decisão'),
  ('estimativa_fiscal',        'transversal',  'analitico',     'Estimativa fiscal quantificada'),
  ('nota_tecnica_fiscal',      'transversal',  'editorial',     'Nota técnica sobre impacto fiscal'),
  ('ente_orcamentario',        'transversal',  'estrutural',    'Ente ou centro de impacto orçamentário'),
  ('resultado_decisorio',      'juridico',     'preditivo',     'Sinal de resultado de julgamento'),
  ('fundamento',               'juridico',     'argumentativo', 'Fundamento jurídico'),
  ('tese',                     'juridico',     'argumentativo', 'Tese fixada ou proposta');

-- actor_types (6)
INSERT INTO actor_types (type_slug, domain_slug, actor_class, label) VALUES
  ('ministro_stf',      'juridico',     'institucional', 'Ministro do STF'),
  ('presidente',        'executivo',    'institucional', 'Presidente da República'),
  ('procurador_geral',  'mp',           'institucional', 'Procurador-Geral da República'),
  ('senador',           'legislativo',  'institucional', 'Senador'),
  ('deputado',          'legislativo',  'institucional', 'Deputado Federal'),
  ('sistema',           'transversal',  'automatizado',  'Ator automatizado (pipeline, IA)');

-- event_types (13)
INSERT INTO event_types (type_slug, domain_slug, event_class, label) VALUES
  ('julgamento',                'juridico',     'juridico',    'Julgamento'),
  ('distribuicao',              'juridico',     'juridico',    'Distribuição'),
  ('publicacao_dje',            'juridico',     'juridico',    'Publicação no DJe'),
  ('promulgacao',               'normativo',    'normativo',   'Promulgação'),
  ('emenda_aplicada',           'normativo',    'normativo',   'Aplicação de emenda constitucional'),
  ('nomeacao',                  'executivo',    'juridico',    'Nomeação'),
  ('mudanca_estado',            'transversal',  'manutencao',  'Transição de estado'),
  ('correcao',                  'transversal',  'manutencao',  'Correção de dado existente'),
  ('anulacao',                  'transversal',  'manutencao',  'Anulação de dado incorreto'),
  ('criacao',                   'transversal',  'manutencao',  'Registro de criação'),
  ('alocacao_risco_fiscal',     'juridico',     'fiscal',      'Redistribuição de risco fiscal'),
  ('modulacao_efeitos_fiscais', 'juridico',     'fiscal',      'Modulação de efeitos com impacto fiscal'),
  ('formacao_resultado',        'juridico',     'juridico',    'Formação de resultado decisório');

-- edge_types (31)
INSERT INTO edge_types (type_slug, source_domain_slug, target_domain_slug, epistemic_class, label, bidirectional, allows_multiple, weight_semantics, weight_required) VALUES
  ('parent_of',                NULL,           NULL,           'estrutural',      'relação hierárquica',                    false, false, NULL,                false),
  ('version_of',               'normativo',    'normativo',    'estrutural',      'versão de uma obra',                     false, false, NULL,                false),
  ('amends',                   'normativo',    'normativo',    'normativa',       'emenda altera dispositivo',              false, true,  NULL,                false),
  ('emenda',                   'legislativo',  'normativo',    'normativa',       'emenda constituição',                    false, true,  NULL,                false),
  ('veta',                     'executivo',    'legislativo',  'normativa',       'veta projeto',                           false, false, NULL,                false),
  ('interpreta',               'juridico',     'normativo',    'interpretativa',  'interpreta dispositivo',                 false, true,  'confidence (0-1)',  true),
  ('aplica',                   'juridico',     'normativo',    'interpretativa',  'aplica norma',                           false, true,  'confidence (0-1)',  true),
  ('questiona',                'juridico',     'normativo',    'interpretativa',  'questiona constitucionalidade',          false, true,  'confidence (0-1)',  true),
  ('sobre',                    NULL,           NULL,           'classificatoria', 'vincula a subject/tema',                 false, true,  'relevancia (0-1)',  false),
  ('annota',                   NULL,           NULL,           'editorial',       'anotação ao alvo',                       false, true,  NULL,                false),
  ('exerce_papel',             NULL,           NULL,           'institucional',   'actor exerce papel em contexto',         false, true,  NULL,                false),
  ('sucede',                   NULL,           NULL,           'institucional',   'actor sucede outro',                     false, false, NULL,                false),
  ('relator_de',               'juridico',     'juridico',     'institucional',   'relator do processo',                    false, false, NULL,                false),
  ('nomeia_ministro',          'executivo',    'juridico',     'institucional',   'nomeia ministro',                        false, false, NULL,                false),
  ('denuncia',                 'mp',           'juridico',     'institucional',   'oferece denúncia',                       false, true,  NULL,                false),
  ('suporta',                  'juridico',     'juridico',     'argumentativa',   'fundamento suporta decisão',             false, true,  'forca (0-1)',       false),
  ('contradiz',                'juridico',     'juridico',     'argumentativa',   'argumento contradiz argumento',          false, true,  'forca (0-1)',       false),
  ('fundamenta_em',            'juridico',     'normativo',    'argumentativa',   'argumento se fundamenta em norma',       false, true,  'confidence (0-1)',  false),
  ('fundamenta',               'juridico',     'juridico',     'argumentativa',   'fundamento embasa decisão',              false, true,  'forca (0-1)',       false),
  ('apoia',                    'juridico',     'juridico',     'argumentativa',   'fundamento/tese apoia outro',            false, true,  'forca (0-1)',       false),
  ('confirma',                 'juridico',     'juridico',     'argumentativa',   'decisão confirma precedente',            false, true,  'confidence (0-1)',  false),
  ('supera',                   'juridico',     'juridico',     'argumentativa',   'decisão supera precedente',              false, true,  'confidence (0-1)',  false),
  ('impacta_orcamento',        'juridico',     'transversal',  'fiscal',          'decisão impacta orçamento de ente',      false, true,  'magnitude (0-1)',   true),
  ('aloca_risco_fiscal',       'juridico',     'transversal',  'fiscal',          'decisão redistribui risco fiscal',       false, true,  'magnitude (0-1)',   true),
  ('quantifica',               'transversal',  'transversal',  'fiscal',          'vincula estimativa a impacto',           false, true,  'confidence (0-1)',  false),
  ('mitiga_impacto',           'juridico',     'juridico',     'fiscal',          'modulação mitiga impacto fiscal',        false, true,  'eficacia (0-1)',    false),
  ('externaliza_risco',        'juridico',     'transversal',  'fiscal',          'decisão transfere risco a terceiro',     false, true,  'magnitude (0-1)',   false),
  ('decide_em_favor_de',       'juridico',     'transversal',  'preditiva',       'decisão favorece parte/ente',            false, true,  'confidence (0-1)',  false),
  ('gera_impacto_orcamentario','juridico',     'transversal',  'fiscal',          'decisão gera impacto orçamentário',      false, true,  'magnitude (0-1)',   false),
  ('modula',                   'juridico',     'juridico',     'fiscal',          'decisão modula efeitos',                 false, true,  'eficacia (0-1)',    false);

-- state_types (9)
INSERT INTO state_types (type_slug, object_type_slug, domain_slug, label, terminal) VALUES
  ('vigente',      'artigo',       'normativo', 'Vigente',                   false),
  ('vigente',      'inciso',       'normativo', 'Vigente',                   false),
  ('vigente',      'paragrafo',    'normativo', 'Vigente',                   false),
  ('suspensa',     'artigo',       'normativo', 'Suspensa por liminar',      false),
  ('revogada',     'artigo',       'normativo', 'Revogada',                  true),
  ('distribuida',  'acao_direta',  'juridico',  'Distribuída',               false),
  ('pautada',      'acao_direta',  'juridico',  'Pautada',                   false),
  ('julgada',      'acao_direta',  'juridico',  'Julgada',                   false),
  ('transitada',   'acao_direta',  'juridico',  'Transitada em julgado',     true);
