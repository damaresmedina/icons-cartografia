-- ============================================================
-- ICONS — Migration 009: Segurança (RLS)
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md
-- Leitura pública + escrita via service_role em todas as tabelas
-- ============================================================

-- ── Habilitar RLS ──

ALTER TABLE domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE object_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE actor_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE edge_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE state_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE objects ENABLE ROW LEVEL SECURITY;
ALTER TABLE actors ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE provenance ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE published_objects ENABLE ROW LEVEL SECURITY;
ALTER TABLE learned_decision_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ontology_proposals ENABLE ROW LEVEL SECURITY;

-- ── Leitura pública ──

CREATE POLICY "public_read" ON domains FOR SELECT USING (true);
CREATE POLICY "public_read" ON object_types FOR SELECT USING (true);
CREATE POLICY "public_read" ON actor_types FOR SELECT USING (true);
CREATE POLICY "public_read" ON event_types FOR SELECT USING (true);
CREATE POLICY "public_read" ON edge_types FOR SELECT USING (true);
CREATE POLICY "public_read" ON state_types FOR SELECT USING (true);
CREATE POLICY "public_read" ON objects FOR SELECT USING (true);
CREATE POLICY "public_read" ON actors FOR SELECT USING (true);
CREATE POLICY "public_read" ON events FOR SELECT USING (true);
CREATE POLICY "public_read" ON edges FOR SELECT USING (true);
CREATE POLICY "public_read" ON provenance FOR SELECT USING (true);
CREATE POLICY "public_read" ON chunks FOR SELECT USING (true);
CREATE POLICY "public_read" ON embeddings FOR SELECT USING (true);
CREATE POLICY "public_read" ON published_objects FOR SELECT USING (true);
CREATE POLICY "public_read" ON learned_decision_profiles FOR SELECT USING (true);
CREATE POLICY "public_read" ON ontology_proposals FOR SELECT USING (true);

-- ── Escrita via service_role ──

CREATE POLICY "service_write" ON domains FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON object_types FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON actor_types FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON event_types FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON edge_types FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON state_types FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON objects FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON actors FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON events FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON edges FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON provenance FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON chunks FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON embeddings FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON published_objects FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON learned_decision_profiles FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_write" ON ontology_proposals FOR ALL USING (auth.role() = 'service_role');
