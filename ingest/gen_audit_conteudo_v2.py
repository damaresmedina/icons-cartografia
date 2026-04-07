"""Gera HTML de auditoria de conteúdo — versão paginada com JSON embutido."""
import sqlite3
import html as ht
import json
from pathlib import Path
from collections import defaultdict

DB = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")
OUT = Path(r"C:\projetos\icons\ingest\audit-deploy\index.html")

con = sqlite3.connect(str(DB))

rows = con.execute("""
    SELECT block_id, anchor_slug, anchor_quality_recode, anchor_source,
           decision_explicitness, decision_unit_type, editorial_marker,
           process_key, relator, block_text, metadata_text,
           LENGTH(block_text) as text_len
    FROM decision_blocks_resolved
    ORDER BY anchor_slug, block_id
""").fetchall()

total = len(rows)
vazios = sum(1 for r in rows if not r[9])
total_chars = sum(len(r[9] or "") for r in rows)

# Group by slug
by_slug = defaultdict(list)
for r in rows:
    slug = r[1] or "(sem slug)"
    by_slug[slug].append({
        "id": r[0], "qr": r[2] or "", "src": r[3] or "", "expl": r[4] or "",
        "dut": r[5] or "", "ed": r[6] or "", "pk": r[7] or "",
        "rel": r[8] or "", "text": r[9] or "", "meta": r[10] or "",
        "len": r[11] or 0,
    })

slug_list = sorted(by_slug.keys())
slug_counts = {s: len(by_slug[s]) for s in slug_list}

# Build JSON data — compressed
data_json = json.dumps(dict(by_slug), ensure_ascii=False, separators=(",", ":"))

con.close()

# Nav items
nav_html = "\n".join(
    f'<a href="#" class="nav-item" data-slug="{ht.escape(s)}">'
    f'{ht.escape(s)} <span class="nav-count">{slug_counts[s]}</span></a>'
    for s in slug_list
)

page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>ICONS — Auditoria de Conteudo</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f5f5f5; color: #222; display: flex; height: 100vh; overflow: hidden; }}
.sidebar {{ width: 280px; background: #fff; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; flex-shrink: 0; }}
.sidebar-header {{ padding: 12px 16px; border-bottom: 1px solid #e0e0e0; }}
.sidebar-header h1 {{ font-size: 16px; }}
.sidebar-header p {{ font-size: 12px; color: #888; margin-top: 4px; }}
#nav-search {{ width: calc(100% - 24px); margin: 8px 12px; padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }}
.nav-list {{ flex: 1; overflow-y: auto; }}
.nav-item {{ display: flex; justify-content: space-between; padding: 5px 16px; font-size: 12px; color: #333; text-decoration: none; border-left: 3px solid transparent; cursor: pointer; }}
.nav-item:hover {{ background: #f0f7ff; border-left-color: #1a73e8; }}
.nav-item.active {{ background: #e8f0fe; border-left-color: #1a73e8; font-weight: 600; }}
.nav-count {{ background: #e8eaed; border-radius: 10px; padding: 1px 7px; font-size: 11px; color: #666; }}
.main {{ flex: 1; overflow-y: auto; padding: 20px 28px; }}
.stats {{ display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }}
.stat {{ background: #fff; border-radius: 8px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
.stat .num {{ font-size: 22px; font-weight: 700; color: #1a73e8; }}
.stat .label {{ font-size: 11px; color: #888; }}
#content-search {{ width: 100%; padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; margin-bottom: 16px; }}
#content-search:focus {{ outline: none; border-color: #1a73e8; }}
.slug-title {{ font-size: 18px; color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 6px; margin-bottom: 14px; }}
.slug-count {{ font-size: 12px; color: #888; font-weight: 400; margin-left: 8px; }}
.block {{ background: #fff; border-radius: 6px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,.06); border-left: 4px solid #1a73e8; }}
.block.empty {{ border-left-color: #dc3545; background: #fff8f8; }}
.block-header {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }}
.block-id {{ font-weight: 700; font-size: 12px; color: #555; }}
.block-type {{ font-size: 11px; color: #7b1fa2; font-weight: 600; }}
.block-pk {{ font-size: 11px; color: #00695c; font-weight: 600; }}
.block-rel {{ font-size: 11px; color: #555; }}
.block-len {{ font-size: 11px; color: #999; margin-left: auto; }}
.block-meta {{ font-size: 12px; color: #666; background: #f8f9fa; padding: 6px 10px; border-radius: 4px; margin-bottom: 8px; font-style: italic; }}
.block-text {{ font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }}
.warn {{ color: #dc3545; font-style: italic; }}
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
#placeholder {{ color: #aaa; font-size: 15px; margin-top: 40px; text-align: center; }}
mark {{ background: #fff176; padding: 1px 2px; border-radius: 2px; }}
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-header">
    <h1>Artigos</h1>
    <p>{len(slug_list)} slugs / {total:,} blocos</p>
  </div>
  <input type="text" id="nav-search" placeholder="Buscar artigo...">
  <div class="nav-list" id="nav-list">
    {nav_html}
  </div>
</div>

<div class="main" id="main">
  <div class="stats">
    <div class="stat"><div class="num">{total:,}</div><div class="label">Blocos</div></div>
    <div class="stat"><div class="num">{total - vazios:,}</div><div class="label">Com texto</div></div>
    <div class="stat"><div class="num">{vazios}</div><div class="label">Vazios</div></div>
    <div class="stat"><div class="num">{total_chars:,}</div><div class="label">Chars totais</div></div>
    <div class="stat"><div class="num">{len(slug_list)}</div><div class="label">Slugs</div></div>
  </div>
  <input type="text" id="content-search" placeholder="Buscar no conteudo dos blocos exibidos...">
  <div id="content">
    <p id="placeholder">Selecione um artigo na sidebar para visualizar seus blocos.</p>
  </div>
</div>

<script>
const DATA = {data_json};

const navItems = document.querySelectorAll('.nav-item');
const navSearch = document.getElementById('nav-search');
const contentSearch = document.getElementById('content-search');
const content = document.getElementById('content');
let currentSlug = null;

function esc(s) {{
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}}

function highlight(text, q) {{
  if (!q) return esc(text);
  const escaped = esc(text);
  const re = new RegExp('(' + q.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');
  return escaped.replace(re, '<mark>$1</mark>');
}}

function renderSlug(slug, searchQ) {{
  const blocks = DATA[slug];
  if (!blocks) return;
  currentSlug = slug;

  navItems.forEach(a => a.classList.toggle('active', a.dataset.slug === slug));

  const q = (searchQ || '').toLowerCase();
  const filtered = q ? blocks.filter(b => (b.text + b.meta + b.pk + b.rel).toLowerCase().includes(q)) : blocks;

  let html = '<h2 class="slug-title">' + esc(slug) +
    '<span class="slug-count">' + filtered.length + ' de ' + blocks.length + ' blocos</span></h2>';

  filtered.forEach(b => {{
    const isEmpty = !b.text.trim();
    html += '<div class="block' + (isEmpty ? ' empty' : '') + '">';
    html += '<div class="block-header">';
    html += '<span class="block-id">#' + b.id + '</span>';
    html += '<span class="tag tag-' + (b.qr || 'unresolved') + '">' + esc(b.qr || '?') + '</span>';
    html += '<span class="tag tag-' + (b.src || 'none') + '">' + esc(b.src || '?') + '</span>';
    html += '<span class="tag tag-' + (b.expl || 'none') + '">' + esc(b.expl || '?') + '</span>';
    html += '<span class="block-type">' + esc(b.dut) + '</span>';
    if (b.pk) html += '<span class="block-pk">' + esc(b.pk) + '</span>';
    if (b.rel) html += '<span class="block-rel">rel. ' + esc(b.rel) + '</span>';
    html += '<span class="block-len">' + b.len.toLocaleString() + ' chars</span>';
    html += '</div>';
    if (b.meta) html += '<div class="block-meta">' + highlight(b.meta, q) + '</div>';
    html += '<div class="block-text">' + (isEmpty ? '<em class="warn">(VAZIO)</em>' : highlight(b.text, q)) + '</div>';
    html += '</div>';
  }});

  content.innerHTML = html;
}}

// Nav click
navItems.forEach(a => {{
  a.addEventListener('click', e => {{
    e.preventDefault();
    renderSlug(a.dataset.slug);
    window.location.hash = a.dataset.slug.replace(/\\./g, '_').replace(/-/g, '_');
  }});
}});

// Nav search
navSearch.addEventListener('input', () => {{
  const q = navSearch.value.toLowerCase();
  navItems.forEach(a => {{
    a.style.display = a.dataset.slug.toLowerCase().includes(q) ? '' : 'none';
  }});
}});

// Content search
let searchTimeout;
contentSearch.addEventListener('input', () => {{
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {{
    if (currentSlug) renderSlug(currentSlug, contentSearch.value);
  }}, 300);
}});

// Hash navigation
function loadFromHash() {{
  const hash = window.location.hash.slice(1);
  if (!hash) return;
  const slug = Object.keys(DATA).find(s =>
    s.replace(/\\./g, '_').replace(/-/g, '_') === hash || s === hash
  );
  if (slug) renderSlug(slug);
}}
window.addEventListener('hashchange', loadFromHash);
loadFromHash();
</script>
</body></html>"""

OUT.write_text(page, encoding="utf-8")
sz = OUT.stat().st_size
print(f"Gerado: {OUT}")
print(f"Tamanho: {sz:,} bytes ({sz/1024/1024:.1f} MB)")
print(f"Slugs: {len(slug_list)}, Blocos: {total}, Vazios: {vazios}")
