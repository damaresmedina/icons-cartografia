import http from 'http';
import fs from 'fs';
import path from 'path';

const ROOT = 'C:/projetos/icons';
const PORT = 8080;

const TYPES = {
  '.html':'text/html','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript',
  '.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg',
  '.woff2':'font/woff2','.ico':'image/x-icon'
};

http.createServer((req, res) => {
  let urlPath = decodeURIComponent(req.url.split('?')[0]);
  if (urlPath === '/') urlPath = '/cartografia_sistema.html';
  const filePath = path.join(ROOT, urlPath);
  if (!filePath.startsWith(path.resolve(ROOT))) { res.writeHead(403).end(); return; }
  fs.stat(filePath, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404, {'Content-Type':'text/plain;charset=utf-8'}).end('404 - '+urlPath); return; }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {'Content-Type': (TYPES[ext]||'application/octet-stream')+'; charset=utf-8', 'Cache-Control':'no-cache'});
    fs.createReadStream(filePath).pipe(res);
  });
}).listen(PORT, '127.0.0.1', () => {
  console.log(`[ICONS local] serving ${ROOT} at http://localhost:${PORT}/`);
});
