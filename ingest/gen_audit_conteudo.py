"""Gera HTML de auditoria do conteúdo textual dos decision_blocks_resolved."""
import sqlite3
import html as ht
from pathlib import Path
from collections import defaultdict

DB = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")
OUT = Path(r"C:\projetos\icons\ingest\audit-deploy\index.html")

con = sqlite3.connect(str(DB))

EDITORIAL_ORDER = """
    CASE decision_unit_type
        WHEN 'sumula_vinculante' THEN 1
        WHEN 'sumula' THEN 2
        WHEN 'controle_concentrado' THEN 3
        WHEN 'repercussao_geral' THEN 4
        WHEN 'julgado_correlato' THEN 5
        WHEN 'julgado_principal' THEN 6
        WHEN 'comentario_editorial' THEN 7
        ELSE 8
    END
"""

rows = con.execute(f"""
    SELECT block_id, anchor_slug, anchor_quality_recode, anchor_source,
           decision_explicitness, decision_unit_type, editorial_marker,
           process_key, relator, block_text, metadata_text,
           LENGTH(block_text) as text_len
    FROM decision_blocks_resolved
    ORDER BY anchor_slug, {EDITORIAL_ORDER}, block_id
""").fetchall()

# Stats
total = len(rows)
vazios = sum(1 for r in rows if not r[9])
total_chars = sum(len(r[9] or "") for r in rows)

# Group by slug
by_slug = defaultdict(list)
for r in rows:
    by_slug[r[1] or "(sem slug)"].append(r)

slug_list = sorted(by_slug.keys())
con.close()

# Build nav + content
nav_items = []
content_blocks = []

for slug in slug_list:
    blocks = by_slug[slug]
    slug_id = slug.replace(".", "_").replace("-", "_")
    nav_items.append(
        f'<a href="#{slug_id}" class="nav-item">'
        f'{ht.escape(slug)} <span class="nav-count">{len(blocks)}</span></a>'
    )

    cards = []
    for r in blocks:
        bid, _, qr, src, expl, dut, ed, pk, rel, text, meta, tlen = r
        text = text or ""
        meta = meta or ""
        empty_cls = " empty" if not text.strip() else ""

        cards.append(f"""<div class="block{empty_cls}" data-id="{bid}">
  <div class="block-header">
    <span class="block-id">#{bid}</span>
    <span class="tag tag-{qr or 'unresolved'}">{ht.escape(qr or '?')}</span>
    <span class="tag tag-{src or 'none'}">{ht.escape(src or '?')}</span>
    <span class="tag tag-{expl or 'none'}">{ht.escape(expl or '?')}</span>
    <span class="block-type">{ht.escape(dut or '')}</span>
    {f'<span class="block-pk">{ht.escape(pk)}</span>' if pk else ''}
    {f'<span class="block-rel">rel. {ht.escape(rel)}</span>' if rel else ''}
    <span class="block-len">{tlen:,} chars</span>
  </div>
  {f'<div class="block-meta">{ht.escape(meta)}</div>' if meta else ''}
  <div class="block-text">{"<em class=\\'warn\\'>(VAZIO)</em>" if not text.strip() else ht.escape(text)}</div>
</div>""")

    content_blocks.append(f"""<div class="slug-section" id="{slug_id}">
  <h2 class="slug-title">{ht.escape(slug)}
    <span class="slug-count">{len(blocks)} bloco{"s" if len(blocks) != 1 else ""}</span>
  </h2>
  {"".join(cards)}
</div>""")

page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>ICONS — Auditoria de Conteudo</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f5f5f5; color: #222; display: flex; height: 100vh; }}

/* Sidebar */
.sidebar {{ width: 280px; background: #fff; border-right: 1px solid #e0e0e0; overflow-y: auto; flex-shrink: 0; padding: 12px 0; }}
.sidebar-header {{ padding: 12px 16px; border-bottom: 1px solid #e0e0e0; }}
.sidebar-header h1 {{ font-size: 16px; }}
.sidebar-header p {{ font-size: 12px; color: #888; margin-top: 4px; }}
#nav-search {{ width: calc(100% - 24px); margin: 8px 12px; padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }}
.nav-item {{ display: flex; justify-content: space-between; padding: 5px 16px; font-size: 12px; color: #333; text-decoration: none; border-left: 3px solid transparent; }}
.nav-item:hover {{ background: #f0f7ff; border-left-color: #1a73e8; }}
.nav-count {{ background: #e8eaed; border-radius: 10px; padding: 1px 7px; font-size: 11px; color: #666; }}

/* Main */
.main {{ flex: 1; overflow-y: auto; padding: 20px 28px; }}

/* Stats bar */
.stats {{ display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }}
.stat {{ background: #fff; border-radius: 8px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
.stat .num {{ font-size: 22px; font-weight: 700; color: #1a73e8; }}
.stat .label {{ font-size: 11px; color: #888; }}

/* Search */
#content-search {{ width: 100%; padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; margin-bottom: 16px; }}
#content-search:focus {{ outline: none; border-color: #1a73e8; }}

/* Slug sections */
.slug-section {{ margin-bottom: 28px; }}
.slug-title {{ font-size: 16px; color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 6px; margin-bottom: 12px; }}
.slug-count {{ font-size: 12px; color: #888; font-weight: 400; margin-left: 8px; }}

/* Blocks */
.block {{ background: #fff; border-radius: 6px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,.06); border-left: 4px solid #1a73e8; }}
.block.empty {{ border-left-color: #dc3545; background: #fff8f8; }}
.block-header {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }}
.block-id {{ font-weight: 700; font-size: 12px; color: #555; }}
.block-type {{ font-size: 11px; color: #7b1fa2; font-weight: 600; }}
.block-pk {{ font-size: 11px; color: #00695c; font-weight: 600; }}
.block-rel {{ font-size: 11px; color: #555; }}
.block-len {{ font-size: 11px; color: #999; margin-left: auto; }}
.block-meta {{ font-size: 12px; color: #666; background: #f8f9fa; padding: 6px 10px; border-radius: 4px; margin-bottom: 8px; font-style: italic; }}
.block-text {{ font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow-y: auto; }}
.block-text .warn {{ color: #dc3545; }}

/* Tags */
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; }}
.tag-exact {{ background: #e6f4ea; color: #1e7e34; }}
.tag-contextual {{ background: #fff3cd; color: #856404; }}
.tag-adct {{ background: #d1ecf1; color: #0c5460; }}
.tag-unresolved {{ background: #f8d7da; color: #721c24; }}
.tag-position {{ background: #e2e3e5; color: #383d41; }}
.tag-hybrid {{ background: #cce5ff; color: #004085; }}
.tag-text {{ background: #d4edda; color: #155724; }}
.tag-explicit {{ background: #d4edda; color: #155724; }}
.tag-implicit {{ background: #e2e3e5; color: #383d41; }}
.tag-none {{ background: #f0f0f0; color: #999; }}

.hidden {{ display: none; }}
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-header">
    <h1>Artigos</h1>
    <p>{len(slug_list)} slugs / {total:,} blocos</p>
  </div>
  <input type="text" id="nav-search" placeholder="Buscar artigo...">
  <div id="nav-list">
    {"".join(nav_items)}
  </div>
</div>

<div class="main">
  <div class="stats">
    <div class="stat"><div class="num">{total:,}</div><div class="label">Blocos</div></div>
    <div class="stat"><div class="num">{total - vazios:,}</div><div class="label">Com texto</div></div>
    <div class="stat"><div class="num">{vazios}</div><div class="label">Vazios</div></div>
    <div class="stat"><div class="num">{total_chars:,}</div><div class="label">Chars totais</div></div>
    <div class="stat"><div class="num">{len(slug_list)}</div><div class="label">Slugs</div></div>
  </div>

  <input type="text" id="content-search" placeholder="Buscar no conteudo dos blocos...">

  <div id="content">
    {"".join(content_blocks)}
  </div>
</div>

<script>
// Nav filter
const navSearch = document.getElementById('nav-search');
const navItems = document.querySelectorAll('.nav-item');
navSearch.addEventListener('input', () => {{
  const q = navSearch.value.toLowerCase();
  navItems.forEach(a => {{
    a.style.display = a.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}});

// Content filter
const contentSearch = document.getElementById('content-search');
const sections = document.querySelectorAll('.slug-section');
contentSearch.addEventListener('input', () => {{
  const q = contentSearch.value.toLowerCase();
  if (!q) {{
    sections.forEach(s => {{ s.style.display = ''; s.querySelectorAll('.block').forEach(b => b.style.display = ''); }});
    return;
  }}
  sections.forEach(s => {{
    let anyVisible = false;
    s.querySelectorAll('.block').forEach(b => {{
      const match = b.textContent.toLowerCase().includes(q);
      b.style.display = match ? '' : 'none';
      if (match) anyVisible = true;
    }});
    s.style.display = anyVisible ? '' : 'none';
  }});
}});
</script>
</body></html>"""

OUT.write_text(page, encoding="utf-8")
print(f"Gerado: {OUT}")
print(f"Tamanho: {len(page):,} chars ({len(page)/1024/1024:.1f} MB)")
print(f"Slugs: {len(slug_list)}, Blocos: {total}, Vazios: {vazios}")
