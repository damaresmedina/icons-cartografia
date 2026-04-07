const fs = require('fs');
const path = require('path');
const dir = path.join('C:', 'projetos', 'icons', 'ingest');

// Read HTML with latin1 encoding
const buf = fs.readFileSync(path.join(dir, 'cf_planalto.html'));
const html = buf.toString('latin1');

// Step 1: Extract all <p> blocks as unified text (join multi-line)
// The Planalto HTML uses <p> tags with content spread across lines
const paragraphs = [];
const pRegex = /<p[^>]*>([\s\S]*?)<\/p>/gi;
let pm;
while ((pm = pRegex.exec(html)) !== null) {
  let text = pm[1]
    .replace(/<[^>]+>/g, '')     // strip all HTML tags
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')
    .trim();
  if (text.length > 0) {
    paragraphs.push(text);
  }
}

console.log('Parágrafos extraídos: ' + paragraphs.length);

// Step 2: Parse each paragraph into the tree
const tree = [];
let currentTitulo = null;
let currentTituloNum = null;
let currentCapitulo = null;
let currentCapituloNum = null;
let currentSecao = null;
let currentSecaoNum = null;
let currentSubsecao = null;
let currentArtigo = null;
let currentArtigoNum = null;
let adct = false;

paragraphs.forEach((text, idx) => {

  // Detect ADCT
  if (text.match(/Ato das Disposi/i) || text.match(/^ADCT/i)) {
    adct = true;
  }

  // PREÂMBULO
  if (text.match(/^Pre[âa]mbulo$/i)) {
    tree.push({
      type: 'preambulo',
      numero: 0,
      text: text,
      depth: 0,
      titulo: null,
      capitulo: null,
      secao: null,
      artigo: null,
      adct: false,
      idx: idx
    });
    return;
  }

  // TÍTULO
  const titMatch = text.match(/^T[ÍI]TULO\s+(I{1,3}V?|VI{0,3}|IX|X{0,3}I{0,3}V?)\s*(.*)/i);
  if (titMatch) {
    currentTituloNum = titMatch[1];
    currentTitulo = text;
    currentCapitulo = null;
    currentCapituloNum = null;
    currentSecao = null;
    currentSecaoNum = null;
    currentSubsecao = null;
    tree.push({
      type: 'titulo',
      numero: currentTituloNum,
      text: text,
      depth: 0,
      titulo: null,
      capitulo: null,
      secao: null,
      artigo: null,
      adct: adct,
      idx: idx
    });
    return;
  }

  // CAPÍTULO
  const capMatch = text.match(/^CAP[ÍI]TULO\s+(I{1,3}V?|VI{0,3}|IX|X{0,3}I{0,3}V?)\s*(.*)/i);
  if (capMatch) {
    currentCapituloNum = capMatch[1];
    currentCapitulo = text;
    currentSecao = null;
    currentSecaoNum = null;
    currentSubsecao = null;
    tree.push({
      type: 'capitulo',
      numero: currentCapituloNum,
      text: text,
      depth: 1,
      titulo: currentTitulo,
      capitulo: null,
      secao: null,
      artigo: null,
      adct: adct,
      idx: idx
    });
    return;
  }

  // SEÇÃO
  const secMatch = text.match(/^Se[çc][ãa]o\s+(I{1,3}V?|VI{0,3}|IX|X{0,3}I{0,3}V?)\s*(.*)/i);
  if (secMatch) {
    currentSecaoNum = secMatch[1];
    currentSecao = text;
    currentSubsecao = null;
    tree.push({
      type: 'secao',
      numero: currentSecaoNum,
      text: text,
      depth: 2,
      titulo: currentTitulo,
      capitulo: currentCapitulo,
      secao: null,
      artigo: null,
      adct: adct,
      idx: idx
    });
    return;
  }

  // SUBSEÇÃO
  const subMatch = text.match(/^Subse[çc][ãa]o\s+(I{1,3}V?|VI{0,3}|IX|X{0,3}I{0,3}V?)\s*(.*)/i);
  if (subMatch) {
    currentSubsecao = text;
    tree.push({
      type: 'subsecao',
      numero: subMatch[1],
      text: text,
      depth: 3,
      titulo: currentTitulo,
      capitulo: currentCapitulo,
      secao: currentSecao,
      artigo: null,
      adct: adct,
      idx: idx
    });
    return;
  }

  // ARTIGO
  const artMatch = text.match(/^Art\.?\s*(\d+)[º°.\s]/);
  if (artMatch) {
    currentArtigoNum = parseInt(artMatch[1]);
    currentArtigo = 'Art. ' + currentArtigoNum;
    tree.push({
      type: 'artigo',
      numero: currentArtigoNum,
      text: text.substring(0, 800),
      depth: 4,
      titulo: currentTitulo,
      capitulo: currentCapitulo,
      secao: currentSecao,
      artigo: null,
      adct: adct,
      idx: idx
    });
    return;
  }

  // PARÁGRAFO ÚNICO
  const parUnicoMatch = text.match(/^Par[áa]grafo [úu]nico[.\s]/i);
  if (parUnicoMatch && currentArtigo) {
    tree.push({
      type: 'paragrafo',
      numero: 'unico',
      text: text.substring(0, 800),
      depth: 5,
      titulo: currentTitulo,
      capitulo: currentCapitulo,
      secao: currentSecao,
      artigo: currentArtigo,
      adct: adct,
      idx: idx
    });
    return;
  }

  // PARÁGRAFO NUMERADO
  const parMatch = text.match(/^§\s*(\d+)[º°.\s]/);
  if (parMatch && currentArtigo) {
    tree.push({
      type: 'paragrafo',
      numero: parseInt(parMatch[1]),
      text: text.substring(0, 800),
      depth: 5,
      titulo: currentTitulo,
      capitulo: currentCapitulo,
      secao: currentSecao,
      artigo: currentArtigo,
      adct: adct,
      idx: idx
    });
    return;
  }

  // INCISO (romano + travessão)
  const incMatch = text.match(/^((?:X{0,3}L?)((?:IX|IV|V?I{0,3})))\s*[-–—]\s*(.*)/);
  if (incMatch && incMatch[1].length > 0 && incMatch[1].length <= 7 && currentArtigo) {
    // Validate it's actually a roman numeral
    const rom = incMatch[1].trim();
    if (rom.match(/^[IVXLC]+$/)) {
      tree.push({
        type: 'inciso',
        numero: rom,
        text: text.substring(0, 800),
        depth: 5,
        titulo: currentTitulo,
        capitulo: currentCapitulo,
        secao: currentSecao,
        artigo: currentArtigo,
        adct: adct,
        idx: idx
      });
      return;
    }
  }

  // ALÍNEA
  const aliMatch = text.match(/^([a-z])\)\s*(.*)/);
  if (aliMatch && currentArtigo) {
    tree.push({
      type: 'alinea',
      numero: aliMatch[1],
      text: text.substring(0, 800),
      depth: 6,
      titulo: currentTitulo,
      capitulo: currentCapitulo,
      secao: currentSecao,
      artigo: currentArtigo,
      adct: adct,
      idx: idx
    });
    return;
  }
});

// Stats
console.log('\n=== ÁRVORE NORMATIVA DA CF (v2) ===');
console.log('Total de nós: ' + tree.length);

const typeCount = {};
tree.forEach(n => { typeCount[n.type] = (typeCount[n.type] || 0) + 1; });
console.log('\nPor tipo:');
Object.entries(typeCount).sort((a,b) => b[1] - a[1]).forEach(([t, c]) => {
  console.log('  ' + c.toString().padStart(6) + '  ' + t);
});

// Check article completeness
const artigos = tree.filter(n => n.type === 'artigo');
const artigosNums = artigos.map(a => a.numero).sort((a,b) => a-b);
const cfArtigos = artigos.filter(a => !a.adct);
const adctArtigos = artigos.filter(a => a.adct);
console.log('\nArtigos CF corpo: ' + cfArtigos.length + ' (max: ' + Math.max(...cfArtigos.map(a=>a.numero)) + ')');
console.log('Artigos ADCT: ' + adctArtigos.length + ' (max: ' + Math.max(...adctArtigos.map(a=>a.numero)) + ')');

// Find gaps in CF body articles
const cfNums = cfArtigos.map(a => a.numero);
const gaps = [];
for (let i = 1; i <= Math.max(...cfNums); i++) {
  if (!cfNums.includes(i)) gaps.push(i);
}
if (gaps.length > 0) {
  console.log('Artigos faltantes no corpo: ' + gaps.length + ' → ' + gaps.slice(0, 20).join(', ') + (gaps.length > 20 ? '...' : ''));
}

// Show tree sample
console.log('\n=== AMOSTRA DA ÁRVORE ===');
tree.slice(0, 40).forEach(n => {
  const indent = '  '.repeat(n.depth);
  console.log(indent + '[' + n.type + (n.numero ? ' ' + n.numero : '') + '] ' + n.text.substring(0, 70));
});

// Save as TSV
let tsv = '\uFEFF' + 'index\ttipo\tnumero\ttexto\tdepth\ttitulo\tcapitulo\tsecao\tartigo\tadct\n';
tree.forEach((n, i) => {
  tsv += (i+1) + '\t' +
    n.type + '\t' +
    (n.numero || '') + '\t' +
    n.text.substring(0, 400).replace(/\t/g, ' ').replace(/\n/g, ' ') + '\t' +
    n.depth + '\t' +
    (n.titulo || '').substring(0, 60).replace(/\t/g, ' ') + '\t' +
    (n.capitulo || '').substring(0, 60).replace(/\t/g, ' ') + '\t' +
    (n.secao || '').substring(0, 60).replace(/\t/g, ' ') + '\t' +
    (n.artigo || '') + '\t' +
    (n.adct ? 'ADCT' : 'CF') + '\n';
});
fs.writeFileSync(path.join(dir, '13_cf_arvore_normativa.csv'), tsv, 'utf8');
fs.writeFileSync(path.join(dir, '13_cf_arvore.json'), JSON.stringify(tree, null, 2), 'utf8');

console.log('\nSalvo: 13_cf_arvore_normativa.csv + 13_cf_arvore.json');
