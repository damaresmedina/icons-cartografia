"""Gera HTML interativo de auditoria do decision_blocks_resolved."""
import sqlite3
import html as h
from pathlib import Path

DB = Path(r"C:\projetos\icons\ingest\saida_parser\cf_comentada_v3.db")
OUT = Path(r"C:\projetos\icons\ingest\decision_blocks_resolved_audit.html")

con = sqlite3.connect(str(DB))
total = con.execute("SELECT COUNT(*) FROM decision_blocks_resolved").fetchone()[0]

def dist(col):
    return con.execute(
        f"SELECT {col}, COUNT(*) as n FROM decision_blocks_resolved GROUP BY {col} ORDER BY n DESC"
    ).fetchall()

quality_dist = dist("anchor_quality_recode")
source_dist = dist("anchor_source")
explicit_dist = dist("decision_explicitness")
status_dist = dist("anchor_resolution_status")
dut_dist = dist("decision_unit_type")
top_slugs = con.execute(
    "SELECT anchor_slug, COUNT(*) as n FROM decision_blocks_resolved "
    "WHERE anchor_slug != '' GROUP BY anchor_slug ORDER BY n DESC LIMIT 20"
).fetchall()

rows = con.execute("""
    SELECT block_id, anchor_slug, anchor_quality_recode, anchor_source,
           decision_explicitness, anchor_resolution_status, decision_unit_type,
           editorial_marker, process_key, relator, namespace,
           LENGTH(block_text) as text_len, substr(block_text, 1, 120) as preview
    FROM decision_blocks_resolved ORDER BY block_id
""").fetchall()
con.close()


def bar_html(items, total_n, color):
    parts = []
    for name, n in items:
        pct = n / total_n * 100
        label = h.escape(str(name or "(vazio)"))
        parts.append(
            f'<div style="margin:4px 0">'
            f'<span style="display:inline-block;width:180px;font-size:13px">{label}</span>'
            f'<span style="display:inline-block;background:{color};height:18px;'
            f'width:{pct*3}px;border-radius:3px"></span>'
            f' <span style="font-size:12px;color:#666">{n:,} ({pct:.1f}%)</span></div>'
        )
    return "\n".join(parts)


def tag(val, prefix):
    v = (val or "").strip()
    cls = prefix + "-" + (v or "unresolved").replace(" ", "")
    return f'<span class="tag {cls}">{h.escape(v or "(vazio)")}</span>'


# Build table rows
tr_lines = []
for r in rows:
    bid, slug, qr, src, expl, status, dut, ed, pk, rel, ns, tlen, preview = r
    cells = [
        str(bid),
        f'<span title="{h.escape(str(slug or ""))}">{h.escape(str(slug or ""))}</span>',
        tag(qr, "tag"),
        tag(src, "tag"),
        tag(expl, "tag"),
        tag(status, "tag"),
        h.escape(str(dut or "")),
        h.escape(str(ed or "")),
        h.escape(str(pk or "")),
        h.escape(str(rel or "")),
        str(ns or ""),
        f"{tlen:,}",
        f'<span title="{h.escape(str(preview or ""))}">{h.escape(str(preview or ""))}</span>',
    ]
    tr_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")

table_body = "\n".join(tr_lines)

page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>ICONS — decision_blocks_resolved</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f5f5f5; color: #222; padding: 24px; }}
h1 {{ font-size: 22px; margin-bottom: 6px; }}
h2 {{ font-size: 15px; margin: 18px 0 8px; color: #555; text-transform: uppercase; letter-spacing: 1px; }}
.stats {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0; }}
.stat {{ background: #fff; border-radius: 8px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.1); min-width: 140px; }}
.stat .num {{ font-size: 28px; font-weight: 700; color: #1a73e8; }}
.stat .label {{ font-size: 12px; color: #888; margin-top: 2px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; margin: 16px 0; }}
.card {{ background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
.card h3 {{ font-size: 13px; color: #555; margin-bottom: 10px; text-transform: uppercase; letter-spacing: .5px; }}
#search {{ width: 100%; padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; margin: 12px 0; }}
#search:focus {{ outline: none; border-color: #1a73e8; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
th {{ background: #f8f9fa; padding: 10px 8px; text-align: left; border-bottom: 2px solid #e0e0e0; position: sticky; top: 0; cursor: pointer; white-space: nowrap; }}
th:hover {{ background: #e8eaed; }}
td {{ padding: 7px 8px; border-bottom: 1px solid #f0f0f0; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
tr:hover td {{ background: #f0f7ff; }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }}
.tag-exact {{ background: #e6f4ea; color: #1e7e34; }}
.tag-contextual {{ background: #fff3cd; color: #856404; }}
.tag-adct {{ background: #d1ecf1; color: #0c5460; }}
.tag-unresolved {{ background: #f8d7da; color: #721c24; }}
.tag-resolved {{ background: #e6f4ea; color: #1e7e34; }}
.tag-implicit {{ background: #e2e3e5; color: #383d41; }}
.tag-hybrid {{ background: #cce5ff; color: #004085; }}
.tag-explicit {{ background: #d4edda; color: #155724; }}
.tag-position {{ background: #e2e3e5; color: #383d41; }}
.tag-text {{ background: #d4edda; color: #155724; }}
#count {{ font-size: 13px; color: #888; margin: 6px 0; }}
.table-wrap {{ max-height: 70vh; overflow-y: auto; }}
</style>
</head>
<body>

<h1>ICONS — decision_blocks_resolved</h1>
<p style="color:#666;font-size:13px">Auditoria do banco cf_comentada_v3.db — {total:,} blocos</p>

<div class="stats">
  <div class="stat"><div class="num">{total:,}</div><div class="label">Blocos totais</div></div>
  <div class="stat"><div class="num">{status_dist[0][1]:,}</div><div class="label">Resolved</div></div>
  <div class="stat"><div class="num">{quality_dist[0][1]:,}</div><div class="label">Exact</div></div>
  <div class="stat"><div class="num">6.57M</div><div class="label">Chars totais</div></div>
</div>

<div class="cards">
  <div class="card"><h3>anchor_quality_recode</h3>
{bar_html(quality_dist, total, '#1a73e8')}</div>
  <div class="card"><h3>anchor_source</h3>
{bar_html(source_dist, total, '#e8710a')}</div>
  <div class="card"><h3>decision_explicitness</h3>
{bar_html(explicit_dist, total, '#0d904f')}</div>
  <div class="card"><h3>decision_unit_type</h3>
{bar_html(dut_dist, total, '#7b1fa2')}</div>
  <div class="card"><h3>anchor_resolution_status</h3>
{bar_html(status_dist, total, '#c62828')}</div>
  <div class="card"><h3>Top 20 anchor_slug</h3>
{bar_html(top_slugs, total, '#00695c')}</div>
</div>

<h2>Dados</h2>
<input type="text" id="search" placeholder="Filtrar por slug, relator, process_key, tipo...">
<div id="count"></div>
<div class="table-wrap">
<table id="tbl">
<thead><tr>
<th data-col="0">ID</th><th data-col="1">anchor_slug</th><th data-col="2">quality_recode</th>
<th data-col="3">source</th><th data-col="4">explicitness</th><th data-col="5">status</th>
<th data-col="6">unit_type</th><th data-col="7">editorial</th><th data-col="8">process_key</th>
<th data-col="9">relator</th><th data-col="10">ns</th><th data-col="11">len</th><th data-col="12">preview</th>
</tr></thead>
<tbody id="tbody">
{table_body}
</tbody></table></div>

<script>
const tbody = document.getElementById('tbody');
const allRows = [...tbody.querySelectorAll('tr')];
const search = document.getElementById('search');
const countEl = document.getElementById('count');

function doFilter() {{
  const q = search.value.toLowerCase();
  let shown = 0;
  allRows.forEach(tr => {{
    const match = !q || tr.textContent.toLowerCase().includes(q);
    tr.style.display = match ? '' : 'none';
    if (match) shown++;
  }});
  countEl.textContent = shown + ' de ' + allRows.length + ' blocos';
}}

search.addEventListener('input', doFilter);
doFilter();

document.querySelectorAll('th').forEach(th => {{
  th.addEventListener('click', () => {{
    const col = +th.dataset.col;
    const asc = th.dataset.asc !== '1';
    th.dataset.asc = asc ? '1' : '0';
    allRows.sort((a, b) => {{
      let va = a.children[col].textContent;
      let vb = b.children[col].textContent;
      const na = parseFloat(va.replace(/,/g,''));
      const nb = parseFloat(vb.replace(/,/g,''));
      if (!isNaN(na) && !isNaN(nb)) return asc ? na - nb : nb - na;
      return asc ? va.localeCompare(vb) : vb.localeCompare(va);
    }});
    allRows.forEach(tr => tbody.appendChild(tr));
  }});
}});
</script>
</body></html>"""

OUT.write_text(page, encoding="utf-8")
print(f"Gerado: {OUT}")
print(f"Tamanho: {len(page):,} chars ({len(page)/1024/1024:.1f} MB)")
