const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join('C:', 'projetos', 'icons', 'ingest', '00_html_clean.html'), 'utf8');
const docx = fs.readFileSync(path.join('C:', 'projetos', 'icons', 'ingest', '01_raw_text.txt'), 'utf8');
const dir = path.join('C:', 'projetos', 'icons', 'ingest');

// ═══════════════════════════════════════════
// PARTE 1: Extrair processos com classe, numero, URL
// ═══════════════════════════════════════════

const urlProcs = [];
const urlRegex = /href="([^"]*(?:PROCESSO|detalhe|downloadPeca)[^"]*)"/g;
let m;
while ((m = urlRegex.exec(html)) !== null) {
  let url = m[1].replace(/&amp;/g, '&');
  const procMatch = url.match(/PROCESSO=(\d+)/);
  const classeMatch = url.match(/CLASSE=([^&]+)/);
  const incidenteMatch = url.match(/incidente=(\d+)/);
  const pecaMatch = url.match(/downloadPeca.*?id=(\d+)/);
  if (procMatch || incidenteMatch || pecaMatch) {
    urlProcs.push({
      processo: procMatch ? procMatch[1] : '',
      classe: classeMatch ? decodeURIComponent(classeMatch[1].replace(/%2D/g, '-')) : '',
      incidente: incidenteMatch ? incidenteMatch[1] : '',
      peca_id: pecaMatch ? pecaMatch[1] : '',
      url_type: procMatch ? 'processo' : (incidenteMatch ? 'detalhe' : 'peca'),
      url: url.startsWith('http') ? url : 'https://portal.stf.jus.br/processos/' + url.replace(/^\.?\.?\/?/, '')
    });
  }
}

const seenUrl = new Set();
const uniqueProcs = urlProcs.filter(p => {
  const key = p.processo + '|' + p.classe + '|' + p.incidente + '|' + p.peca_id;
  if (seenUrl.has(key)) return false;
  seenUrl.add(key);
  return true;
});

// Text metadata from DOCX brackets
const metaRegex = /\[([A-Z]{2,}[\s-]*(?:AgR|ED|MC|QO|TP|CR)?)\s*[n\u00ba.]*\s*([\d.]+(?:[-\/]\d+)?)[,\s]*(?:rel\.?\s*(?:p\/\s*o?\s*ac\.?\s*)?min\.?\s*([^,\]]+?))?(?:,\s*(?:red\.?\s*(?:p\/\s*o?\s*ac\.?\s*)?min\.?\s*([^,\]]+?))?)?(?:,\s*j\.\s*([^,\]]+?))?(?:,\s*(P|1\u00aa?\s*T|2\u00aa?\s*T|mono[^,\]]*))?\s*(?:,\s*D[Jj][Ee]?\s*de\s*([^,\]]+?))?(?:,\s*[Tt]ema\s*(\d+))?[^\]]*\]/g;

const textProcs = [];
let tm;
while ((tm = metaRegex.exec(docx)) !== null) {
  textProcs.push({
    classe: tm[1].trim(),
    numero: tm[2].trim(),
    relator: tm[3] ? tm[3].trim() : '',
    redator: tm[4] ? tm[4].trim() : '',
    data_julgamento: tm[5] ? tm[5].trim() : '',
    orgao: tm[6] ? tm[6].trim() : '',
    dje: tm[7] ? tm[7].trim() : '',
    tema_rg: tm[8] ? tm[8].trim() : '',
    raw: tm[0].substring(0, 200)
  });
}

const seenText = new Set();
const uniqueTextProcs = textProcs.filter(p => {
  const key = p.classe + ' ' + p.numero;
  if (seenText.has(key)) return false;
  seenText.add(key);
  return true;
});

// Save
let tsvUrl = '\uFEFF' + 'numero\tprocesso\tclasse\tincidente\tpeca_id\turl_type\turl\n';
uniqueProcs.forEach((p, i) => {
  tsvUrl += (i+1) + '\t' + p.processo + '\t' + p.classe + '\t' + p.incidente + '\t' + p.peca_id + '\t' + p.url_type + '\t' + p.url + '\n';
});
fs.writeFileSync(path.join(dir, '07_processos_urls.csv'), tsvUrl, 'utf8');

let tsvText = '\uFEFF' + 'numero\tclasse\tnumero_processo\trelator\tredator\tdata_julgamento\torgao\tdje\ttema_rg\traw\n';
uniqueTextProcs.forEach((p, i) => {
  tsvText += (i+1) + '\t' + p.classe + '\t' + p.numero + '\t' + p.relator + '\t' + p.redator + '\t' + p.data_julgamento + '\t' + p.orgao + '\t' + p.dje + '\t' + p.tema_rg + '\t' + p.raw.replace(/\t/g, ' ') + '\n';
});
fs.writeFileSync(path.join(dir, '08_processos_metadados.csv'), tsvText, 'utf8');

console.log('=== PROCESSOS POR URL ===');
console.log('Total: ' + uniqueProcs.length);
console.log('  processo: ' + uniqueProcs.filter(p => p.url_type === 'processo').length);
console.log('  detalhe: ' + uniqueProcs.filter(p => p.url_type === 'detalhe').length);
console.log('  peca: ' + uniqueProcs.filter(p => p.url_type === 'peca').length);

console.log('\n=== PROCESSOS POR METADADO TEXTUAL ===');
console.log('Total unico: ' + uniqueTextProcs.length);
console.log('Total mencoes: ' + textProcs.length);
console.log('Com relator: ' + uniqueTextProcs.filter(p => p.relator).length);
console.log('Com data: ' + uniqueTextProcs.filter(p => p.data_julgamento).length);
console.log('Com orgao: ' + uniqueTextProcs.filter(p => p.orgao).length);
console.log('Com tema RG: ' + uniqueTextProcs.filter(p => p.tema_rg).length);

const classeCount = {};
uniqueTextProcs.forEach(p => { classeCount[p.classe] = (classeCount[p.classe] || 0) + 1; });
console.log('\n=== POR CLASSE ===');
Object.entries(classeCount).sort((a,b) => b[1] - a[1]).slice(0, 15).forEach(([c, n]) => {
  console.log('  ' + n.toString().padStart(5) + '  ' + c);
});

// ═══════════════════════════════════════════
// PARTE 2: Segmentar em 4 tipos de bloco
// ═══════════════════════════════════════════

const blockRegex2 = /<(?:div|span|p|h\d)[^>]*class="(tit|suTIT|cap|suCAP|sec|suSEC|sse|suSSE|art|inc|par|ali|com-titulo|com|cra|rea)"[^>]*>([\s\S]*?)(?=<(?:div|span|p|h\d)[^>]*class="(?:tit|suTIT|cap|suCAP|sec|suSEC|sse|suSSE|art|inc|par|ali|com-titulo|com|cra|rea)")/g;

const tipoA = [];
const tipoB = [];
const tipoC = [];
const tipoD = [];

let currentNorm = null;
let currentEdit = null;
let bm;
let blockIdx = 0;

while ((bm = blockRegex2.exec(html)) !== null) {
  const cls = bm[1];
  const content = bm[2];
  const text = content.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  if (!text) continue;

  const links = [];
  const lRegex = /href="([^"]*(?:detalhe|downloadPeca|PROCESSO)[^"]*)"/g;
  let lm2;
  while ((lm2 = lRegex.exec(content)) !== null) {
    links.push(lm2[1].replace(/&amp;/g, '&'));
  }

  const bracketMeta = text.match(/\[[A-Z]{2,}[^\]]{5,}\]/g) || [];

  const block = {
    index: blockIdx++,
    html_class: cls,
    norm_anchor: currentNorm ? currentNorm.text : '',
    norm_anchor_type: currentNorm ? currentNorm.type : '',
    editorial_category: currentEdit || '',
    text: text.substring(0, 1000),
    links_count: links.length,
    first_link: links.length > 0 ? links[0] : '',
    bracket_meta: bracketMeta.slice(0, 3).map(b => b.substring(0, 150)).join(' | '),
    has_bracket_meta: bracketMeta.length > 0
  };

  if (['tit', 'suTIT', 'cap', 'suCAP', 'sec', 'suSEC', 'sse', 'suSSE', 'art', 'inc', 'par', 'ali'].includes(cls)) {
    block.block_type = 'A_normativo';
    currentNorm = { type: cls, text: text.substring(0, 100) };
    currentEdit = null;
    tipoA.push(block);
  } else if (cls === 'com-titulo') {
    block.block_type = 'B_editorial';
    const nt = text.toLowerCase().trim();
    if (nt.includes('controle concentrado') || nt.includes('controle de concentrado')) {
      currentEdit = 'controle_concentrado';
    } else if (nt.includes('repercuss')) {
      currentEdit = 'repercussao_geral';
    } else if (nt.includes('julgado') && nt.includes('correlato')) {
      currentEdit = 'julgados_correlatos';
    } else if (nt.includes('mula vinculante') || nt.includes('mulas vinculantes')) {
      currentEdit = 'sumula_vinculante';
    } else if (nt.includes('mula')) {
      currentEdit = 'sumula';
    } else {
      currentEdit = text.substring(0, 80);
    }
    block.editorial_category = currentEdit;
    tipoB.push(block);
  } else if (cls === 'com') {
    if (bracketMeta.length > 0) {
      block.block_type = 'D_metadados';
      tipoD.push(block);
    } else {
      block.block_type = 'C_textual';
      tipoC.push(block);
    }
  } else if (cls === 'cra' || cls === 'rea') {
    block.block_type = 'C_textual';
    tipoC.push(block);
  }
}

console.log('\n=== SEGMENTACAO EM 4 TIPOS ===');
console.log('Tipo A (normativo):  ' + tipoA.length);
console.log('Tipo B (editorial):  ' + tipoB.length);
console.log('Tipo C (textual):    ' + tipoC.length);
console.log('Tipo D (metadados):  ' + tipoD.length);

function saveBlocks(blocks, filename) {
  let tsv = '\uFEFF' + 'index\tblock_type\thtml_class\tnorm_anchor\tnorm_anchor_type\teditorial_category\ttext\tlinks_count\tfirst_link\tbracket_meta\n';
  blocks.forEach(b => {
    tsv += b.index + '\t' +
      b.block_type + '\t' +
      b.html_class + '\t' +
      b.norm_anchor.replace(/\t/g, ' ') + '\t' +
      b.norm_anchor_type + '\t' +
      b.editorial_category.replace(/\t/g, ' ') + '\t' +
      b.text.substring(0, 300).replace(/\t/g, ' ').replace(/\n/g, ' ') + '\t' +
      b.links_count + '\t' +
      b.first_link + '\t' +
      b.bracket_meta.replace(/\t/g, ' ') + '\n';
  });
  fs.writeFileSync(path.join(dir, filename), tsv, 'utf8');
}

saveBlocks(tipoA, '09_tipo_A_normativo.csv');
saveBlocks(tipoB, '10_tipo_B_editorial.csv');
saveBlocks(tipoC, '11_tipo_C_textual.csv');
saveBlocks(tipoD, '12_tipo_D_metadados.csv');

console.log('\nArquivos salvos.');
