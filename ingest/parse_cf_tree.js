const fs = require('fs');
const path = require('path');
const dir = path.join('C:', 'projetos', 'icons', 'ingest');

// Read HTML with latin1 encoding
const buf = fs.readFileSync(path.join(dir, 'cf_planalto.html'));
const html = buf.toString('latin1');

// Extract text blocks - the CF uses <p> tags with specific patterns
const lines = html.split('\n');
const tree = [];

let currentTitulo = null;
let currentCapitulo = null;
let currentSecao = null;
let currentArtigo = null;

lines.forEach((line, idx) => {
  // Strip HTML tags to get text
  const text = line.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
  if (!text) return;

  // PREÂMBULO
  if (text.match(/^Pre[aâ]mbulo$/i)) {
    tree.push({ type: 'preambulo', text: text, depth: 0, parent: null, line: idx });
    return;
  }

  // TÍTULO
  const titMatch = text.match(/^T[IÍ]TULO\s+(I{1,3}V?|VI{0,3}|IX|X)\b/i);
  if (titMatch) {
    currentTitulo = text;
    currentCapitulo = null;
    currentSecao = null;
    tree.push({ type: 'titulo', text: text, depth: 0, parent: null, line: idx });
    return;
  }

  // CAPÍTULO
  const capMatch = text.match(/^CAP[IÍ]TULO\s+(I{1,3}V?|VI{0,3}|IX|X{1,3})\b/i);
  if (capMatch) {
    currentCapitulo = text;
    currentSecao = null;
    tree.push({ type: 'capitulo', text: text, depth: 1, parent: currentTitulo, line: idx });
    return;
  }

  // SEÇÃO
  const secMatch = text.match(/^Se[çc][ãa]o\s+(I{1,3}V?|VI{0,3}|IX|X{1,3})\b/i);
  if (secMatch) {
    currentSecao = text;
    tree.push({ type: 'secao', text: text, depth: 2, parent: currentCapitulo || currentTitulo, line: idx });
    return;
  }

  // SUBSEÇÃO
  const subMatch = text.match(/^Subse[çc][ãa]o\s+(I{1,3}V?|VI{0,3}|IX|X{1,3})\b/i);
  if (subMatch) {
    tree.push({ type: 'subsecao', text: text, depth: 3, parent: currentSecao || currentCapitulo, line: idx });
    return;
  }

  // ARTIGO - Art. Nº
  const artMatch = text.match(/^Art\.?\s*(\d+)[º°.]?\s*(.*)/);
  if (artMatch) {
    currentArtigo = 'Art. ' + artMatch[1];
    const fullText = artMatch[2] ? artMatch[0] : text;
    tree.push({
      type: 'artigo',
      numero: parseInt(artMatch[1]),
      text: fullText.substring(0, 500),
      depth: 3,
      parent_titulo: currentTitulo,
      parent_capitulo: currentCapitulo,
      parent_secao: currentSecao,
      line: idx
    });
    return;
  }

  // PARÁGRAFO
  const parMatch = text.match(/^[§Pp]ar[áa]grafo\s+[úu]nico[.]?\s*(.*)/i) || text.match(/^§\s*(\d+)[º°.]?\s*(.*)/);
  if (parMatch && currentArtigo) {
    tree.push({
      type: 'paragrafo',
      text: text.substring(0, 500),
      depth: 4,
      parent: currentArtigo,
      line: idx
    });
    return;
  }

  // INCISO - romano seguido de travessão ou hífen
  const incMatch = text.match(/^(X{0,3}(?:IX|IV|V?I{0,3}))\s*[-–—]\s*(.*)/);
  if (incMatch && incMatch[1] && currentArtigo) {
    tree.push({
      type: 'inciso',
      numero_romano: incMatch[1],
      text: text.substring(0, 500),
      depth: 4,
      parent: currentArtigo,
      line: idx
    });
    return;
  }

  // ALÍNEA - letra seguida de )
  const aliMatch = text.match(/^([a-z])\)\s*(.*)/);
  if (aliMatch && currentArtigo) {
    tree.push({
      type: 'alinea',
      letra: aliMatch[1],
      text: text.substring(0, 500),
      depth: 5,
      parent: currentArtigo,
      line: idx
    });
    return;
  }
});

console.log('=== ÁRVORE NORMATIVA DA CF ===');
console.log('Total de nós: ' + tree.length);

const typeCount = {};
tree.forEach(n => { typeCount[n.type] = (typeCount[n.type] || 0) + 1; });
console.log('\nPor tipo:');
Object.entries(typeCount).sort((a,b) => b[1] - a[1]).forEach(([t, c]) => {
  console.log('  ' + c.toString().padStart(6) + '  ' + t);
});

// Show first nodes
console.log('\n=== PRIMEIROS 30 NÓS ===');
tree.slice(0, 30).forEach(n => {
  const indent = '  '.repeat(n.depth);
  console.log(indent + '[' + n.type + '] ' + n.text.substring(0, 80));
});

// Save as TSV
let tsv = '\uFEFF' + 'index\ttipo\tnumero\ttexto\tdepth\tparent_titulo\tparent_capitulo\tparent_secao\tparent\tline\n';
tree.forEach((n, i) => {
  tsv += (i+1) + '\t' +
    n.type + '\t' +
    (n.numero || n.numero_romano || n.letra || '') + '\t' +
    n.text.substring(0, 300).replace(/\t/g, ' ').replace(/\n/g, ' ') + '\t' +
    n.depth + '\t' +
    (n.parent_titulo || '') + '\t' +
    (n.parent_capitulo || '') + '\t' +
    (n.parent_secao || '') + '\t' +
    (n.parent || '') + '\t' +
    n.line + '\n';
});
fs.writeFileSync(path.join(dir, '13_cf_arvore_normativa.csv'), tsv, 'utf8');

// Save as JSON for cotejo
fs.writeFileSync(path.join(dir, '13_cf_arvore.json'), JSON.stringify(tree, null, 2), 'utf8');

console.log('\nSalvo: 13_cf_arvore_normativa.csv + 13_cf_arvore.json');
