-- ============================================================
-- ICONS — Cartografia do Litigioso Brasileiro
-- Migration 000: Extensões (pré-condição de infraestrutura)
-- Derivado de: CONSTITUICAO_ONTOLOGICA.md
-- Autora: Damares Medina · 2026
-- ============================================================

-- UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Vector embeddings (§20 Camada 4)
CREATE EXTENSION IF NOT EXISTS vector;

-- Trigram search (busca textual futura)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
