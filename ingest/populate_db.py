"""
populate_db.py
Script completo de limpeza + carga do banco constitucional.
Uso:
    pip install psycopg2-binary   # ou sqlite3 (já incluso no Python)
    python populate_db.py --db sqlite  --out cf_comentada.db
    python populate_db.py --db postgres --dsn "postgresql://user:pw@host/dbname"
"""
import json, csv, re, argparse, sqlite3, sys
from collections import Counter
from pathlib import Path

# ─── Configuração ───────────────────────────────────────────────────────────
BLOCKS_JSON   = "commentary_blocks.json"
ANCHOR_TSV    = "norm_anchor_index.tsv"

# ─── Conversor romano → arábico ─────────────────────────────────────────────
ROMAN = {
    "I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,"VII":7,"VIII":8,"IX":9,"X":10,
    "XI":11,"XII":12,"XIII":13,"XIV":14,"XV":15,"XVI":16,"XVII":17,"XVIII":18,
    "XIX":19,"XX":20,"XXI":21,"XXII":22,"XXIII":23,"XXIV":24,"XXV":25,
    "XXVI":26,"XXVII":27,"XXVIII":28,"XXIX":29,"XXX":30,"XXXI":31,"XXXII":32,
    "XXXIII":33,"XXXIV":34,"XXXV":35,"XXXVI":36,"XXXVII":37,"XXXVIII":38,
    "XXXIX":39,"XL":40,"XLI":41,"XLII":42,"XLIII":43,"XLIV":44,"XLV":45,
    "XLVI":46,"XLVII":47,"XLVIII":48,"XLIX":49,"L":50,"LI":51,"LII":52,
    "LIII":53,"LIV":54,"LV":55,"LVI":56,"LVII":57,"LVIII":58,"LIX":59,
    "LX":60,"LXI":61,"LXII":62,"LXIII":63,"LXIV":64,"LXV":65,"LXVI":66,
    "LXVII":67,"LXVIII":68,"LXIX":69,"LXX":70,"LXXI":71,"LXXII":72,
    "LXXIII":73,"LXXIV":74,"LXXV":75,"LXXVI":76,"LXXVII":77,"LXXVIII":78,
}

# ─── Normalização de slug ────────────────────────────────────────────────────
def normalize_slug(s: str) -> str:
    """
    Corrige dois bugs do parser:
    1. Prefixo  : cf-art-  →  cf-1988-art-
    2. Incisos  : -inc-XIV →  -inc-14
    """
    if not s or s == "adct":
        return s
    # Fix 1
    if s.startswith("cf-art-"):
        s = "cf-1988-" + s[3:]
    # Fix 2
    def _roman(m):
        r = m.group(1).upper()
        return f"-inc-{ROMAN.get(r, r)}"
    s = re.sub(r"-inc-([A-Z]+)", _roman, s)
    return s

def find_best_slug(norm_slug: str, tsv_slugs: set) -> tuple:
    """
    Tenta match exato; se falhar, sobe na hierarquia até encontrar
    o nó pai mais próximo presente no TSV.
    Retorna (slug_matched, match_type)
    """
    if not norm_slug:
        return None, "none"
    if norm_slug == "adct":
        return "adct", "adct"
    if norm_slug in tsv_slugs:
        return norm_slug, "exact"
    parts = norm_slug.split("-")
    for i in range(len(parts) - 1, 3, -1):
        candidate = "-".join(parts[:i])
        if candidate in tsv_slugs:
            return candidate, "parent"
    return None, "none"

# ─── Normalização de data ────────────────────────────────────────────────────
def normalize_date(d) -> str | None:
    """
    Converte D-M-YYYY ou DD-MM-YYYY para ISO 8601 (YYYY-MM-DD).
    Rejeita fragmentos (só dia), anos fora de 1988-2026, e malformados.
    """
    if not d:
        return None
    d = str(d).strip()
    if re.match(r"^\d{1,2}$", d):          # só o dia — fragmento inútil
        return None
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", d)
    if m:
        day, mon, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= day <= 31 and 1 <= mon <= 12 and 1988 <= yr <= 2026:
            return f"{yr:04d}-{mon:02d}-{day:02d}"
    return None

# ─── Pipeline principal ──────────────────────────────────────────────────────
def load_and_clean():
    print("Carregando dados...")
    with open(BLOCKS_JSON, encoding="utf-8") as f:
        raw = json.load(f)

    tsv_info = {}
    with open(ANCHOR_TSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            # guarda só a primeira ocorrência de cada slug
            if r["slug"] not in tsv_info:
                tsv_info[r["slug"]] = r
    tsv_slugs = set(tsv_info.keys())

    # ── Deduplicação ────────────────────────────────────────────────────────
    seen, deduped, n_dup = set(), [], 0
    for b in raw:
        key = (b.get("block_text", "").strip()[:300], b.get("anchor_slug"))
        if key in seen:
            n_dup += 1
            continue
        seen.add(key)
        deduped.append(b)
    print(f"  Duplicatas removidas: {n_dup}. Blocos restantes: {len(deduped)}")

    # ── Enriquecimento ───────────────────────────────────────────────────────
    stats = Counter()
    clean = []
    for b in deduped:
        raw_slug = b.get("anchor_slug")
        norm     = normalize_slug(raw_slug)
        matched, mtype = find_best_slug(norm, tsv_slugs)
        stats[mtype] += 1

        node_type = node_label = None
        if matched and matched in tsv_info:
            node_type  = tsv_info[matched]["node_type"]
            node_label = tsv_info[matched]["label"]
        elif matched == "adct":
            node_type, node_label = "adct", "ADCT"

        # process_full: "ADI 1234" unificado
        pc, pn = b.get("process_class"), b.get("process_number")
        process_full = None
        if pn:
            pn_clean = str(pn).strip().rstrip(".")
            process_full = f"{pc} {pn_clean}" if pc else pn_clean

        clean.append({
            "block_id"            : b["block_id"],
            "anchor_slug_original": raw_slug,
            "anchor_slug"         : matched,
            "anchor_slug_norm"    : norm,
            "match_type"          : mtype,
            "node_type"           : node_type,
            "node_label"          : node_label,
            "anchor_artigo"       : b.get("anchor_artigo"),
            "anchor_paragrafo"    : b.get("anchor_paragrafo"),
            "anchor_inciso"       : b.get("anchor_inciso"),
            "anchor_alinea"       : b.get("anchor_alinea"),
            "editorial_marker"    : b.get("editorial_marker"),
            "block_text"          : b.get("block_text"),
            "metadata_text"       : b.get("metadata_text"),
            "process_class"       : pc,
            "process_number"      : pn,
            "process_full"        : process_full,
            "relator"             : b.get("relator"),
            "data_julgamento_raw" : b.get("data_julgamento"),
            "data_julgamento"     : normalize_date(b.get("data_julgamento")),
            "ano"                 : b.get("ano"),
            "tema"                : b.get("tema"),
            "dje"                 : b.get("dje"),
        })

    print("\n  Match após limpeza:")
    for k, v in stats.most_common():
        print(f"    {k:10s}: {v:5d}  ({v/len(clean)*100:.1f}%)")

    return clean, list(tsv_info.values())

# ─── Carga SQLite ─────────────────────────────────────────────────────────────
SCHEMA_NORM_NODES = """
CREATE TABLE IF NOT EXISTS norm_nodes (
    slug        TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    node_type   TEXT NOT NULL CHECK(node_type IN
                    ('titulo','capitulo','artigo','paragrafo','inciso','alinea','adct'))
);
"""

SCHEMA_BLOCKS = """
CREATE TABLE IF NOT EXISTS commentary_blocks (
    block_id             INTEGER PRIMARY KEY,
    anchor_slug          TEXT REFERENCES norm_nodes(slug),
    anchor_slug_original TEXT,
    anchor_slug_norm     TEXT,
    match_type           TEXT,
    node_type            TEXT,
    node_label           TEXT,
    anchor_artigo        TEXT,
    anchor_paragrafo     TEXT,
    anchor_inciso        TEXT,
    anchor_alinea        TEXT,
    editorial_marker     TEXT,
    block_text           TEXT,
    metadata_text        TEXT,
    process_class        TEXT,
    process_number       TEXT,
    process_full         TEXT,
    relator              TEXT,
    data_julgamento      TEXT,   -- ISO 8601: YYYY-MM-DD
    data_julgamento_raw  TEXT,   -- valor original preservado
    ano                  INTEGER,
    tema                 TEXT,
    dje                  TEXT
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_cb_slug       ON commentary_blocks(anchor_slug);",
    "CREATE INDEX IF NOT EXISTS idx_cb_artigo     ON commentary_blocks(anchor_artigo);",
    "CREATE INDEX IF NOT EXISTS idx_cb_marker     ON commentary_blocks(editorial_marker);",
    "CREATE INDEX IF NOT EXISTS idx_cb_relator    ON commentary_blocks(relator);",
    "CREATE INDEX IF NOT EXISTS idx_cb_class      ON commentary_blocks(process_class);",
    "CREATE INDEX IF NOT EXISTS idx_cb_data       ON commentary_blocks(data_julgamento);",
    "CREATE INDEX IF NOT EXISTS idx_cb_ano        ON commentary_blocks(ano);",
    "CREATE INDEX IF NOT EXISTS idx_cb_proc_full  ON commentary_blocks(process_full);",
    "CREATE VIRTUAL TABLE IF NOT EXISTS cb_fts USING fts5(block_text, content='commentary_blocks', content_rowid='block_id');",
]

FTS_POPULATE = """
INSERT INTO cb_fts(rowid, block_text)
SELECT block_id, block_text FROM commentary_blocks WHERE block_text IS NOT NULL;
"""

def load_sqlite(blocks, nodes, db_path):
    import sqlite3
    print(f"\nCriando banco SQLite: {db_path}")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute(SCHEMA_NORM_NODES)
    cur.execute(SCHEMA_BLOCKS)

    # norm_nodes
    cur.executemany(
        "INSERT OR IGNORE INTO norm_nodes(slug, label, node_type) VALUES (?,?,?)",
        [(r["slug"], r["label"], r["node_type"]) for r in nodes]
    )
    # adct node
    cur.execute("INSERT OR IGNORE INTO norm_nodes VALUES ('adct','ADCT','adct')")
    print(f"  norm_nodes inseridos: {cur.rowcount + len(nodes)}")

    # blocks
    cols = list(blocks[0].keys())
    # remove anchor_slug_norm (não está na tabela, só útil no JSON)
    insert_cols = [c for c in cols if c != "anchor_slug_norm"]
    placeholders = ",".join("?" for _ in insert_cols)
    cur.executemany(
        f"INSERT OR REPLACE INTO commentary_blocks({','.join(insert_cols)}) VALUES ({placeholders})",
        [[b[c] for c in insert_cols] for b in blocks]
    )
    print(f"  commentary_blocks inseridos: {len(blocks)}")

    # indexes
    for idx in INDEXES:
        try:
            cur.execute(idx)
        except Exception as e:
            print(f"  [aviso] índice falhou: {e}")
    # fts
    try:
        cur.execute(FTS_POPULATE)
        print("  FTS (busca full-text) configurado")
    except Exception as e:
        print(f"  [aviso] FTS falhou: {e}")

    con.commit()
    con.close()

    size_mb = Path(db_path).stat().st_size / 1_048_576
    print(f"\n  Banco criado: {db_path}  ({size_mb:.1f} MB)")

# ─── Entrypoint ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Popular banco CF comentada")
    p.add_argument("--db",  default="sqlite", choices=["sqlite","postgres"])
    p.add_argument("--out", default="cf_comentada.db", help="caminho do .db (sqlite)")
    p.add_argument("--dsn", help="DSN postgres: postgresql://user:pw@host/db")
    args = p.parse_args()

    blocks, nodes = load_and_clean()

    if args.db == "sqlite":
        load_sqlite(blocks, nodes, args.out)
    else:
        try:
            import psycopg2
        except ImportError:
            sys.exit("Instale psycopg2-binary para usar postgres.")
        # Adaptação do schema e inserção para postgres
        # (mesma lógica, substituindo ? por %s e CREATE VIRTUAL por pg_trgm)
        print("Postgres: adapte as queries substituindo ? por %s e FTS por pg_trgm/tsvector.")
