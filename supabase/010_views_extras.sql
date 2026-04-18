-- ============================================================
-- ICONS — Migration 010: Views Extras (preservação)
-- ============================================================
-- Gerado em: 2026-04-18T02:42:36.685Z
-- Autora: Damares Medina
-- Origem: extraídas de hetuhkhhppxjliiaerlu.supabase.co (pg_get_viewdef)
-- Motivo: views que existem no banco mas não estavam em migration
--         anterior. Preservação em git para reconstrução se cair.
-- ============================================================

-- ════════════════════════════════════════════════════════════
-- VIEW: v_ancoragem_decisoes
-- ════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW public.v_ancoragem_decisoes AS
SELECT t.slug AS dispositivo,
    s.slug AS decisao_slug,
    COALESCE(NULLIF(m.classe, ''::text), ''::text) AS classe,
    COALESCE(NULLIF(m.numero, ''::text), ''::text) AS numero,
    COALESCE(NULLIF(m.relator, ''::text), ''::text) AS relator,
    COALESCE(NULLIF(m.data_julgamento, ''::text), ''::text) AS data_julgamento,
    COALESCE(NULLIF(m.turma, ''::text), ''::text) AS turma,
    COALESCE(NULLIF(m.referencia, ''::text), s.payload ->> 'rotulo_final'::text, ''::text) AS referencia,
    COALESCE(NULLIF(s.payload ->> 'tipo_decisorio'::text, ''::text), ''::text) AS tipo,
    COALESCE(NULLIF(s.payload ->> 'camada_editorial'::text, ''::text), ''::text) AS camada,
    s.payload ->> 'conteudo'::text AS conteudo
   FROM edges e
     JOIN objects t ON t.id = e.target_id
     JOIN objects s ON s.id = e.source_id
     LEFT JOIN stf_metadados_confirmados m ON m.com_id = ((s.payload ->> 'stf_com_id'::text)::integer)
  WHERE e.type_slug = 'ancora_normativa'::text AND s.type_slug = 'registro_jurisprudencial'::text
  ORDER BY t.slug, ((s.payload ->> 'ordem_editorial'::text)::integer);
