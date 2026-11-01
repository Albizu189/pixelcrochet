const CACHE = 'pixelcrochet-v5';
const CORE = ['/', '/index.html', '/manifest.webmanifest', '/icons/icon.svg', '/algorithms/original_cell.py', '/algorithms/runner.py', '/workers/crochet-worker.js'];

async function precache() {
  const cache = await caches.open(CACHE);
  const response = await fetch('/index.html', { cache: 'no-store' });
  await cache.put('/index.html', response.clone());
  const html = await response.text();
  const assets = [...html.matchAll(/(?:src|href)="([^"#]+)"/g)]
    .map((match) => match[1])
    .filter((path) => (path.startsWith('/') || path.startsWith('./')) && !path.startsWith('//'))
    .map((path) => new URL(path, self.location.origin).pathname);
  await cache.addAll([...new Set([...CORE, ...assets])]);
  for (const cssAsset of assets.filter((asset) => asset.endsWith('.css'))) {
    const cssText = await (await fetch(cssAsset)).text();
    const nested = [...cssText.matchAll(/url\(([^)]+)\)/g)]
      .map((match) => match[1].trim().replace(/["']/g, ''))
      .filter((url) => !url.startsWith('data:'))
      .map((url) => new URL(url, new URL(cssAsset, self.location.origin)))
      .filter((url) => url.origin === self.location.origin)
      .map((url) => url.pathname);
    if (nested.length) await cache.addAll([...new Set(nested)]);
  }
  const manifestResponse = await fetch('/pyodide/manifest.json');
  await cache.put('/pyodide/manifest.json', manifestResponse.clone());
  const manifest = await manifestResponse.json();
  // Chromium can reject Cache.addAll for the largest wheels; cache each buffer explicitly.
  for (const file of manifest.files) {
    const url = `/pyodide/${file}`;
    const packageResponse = await fetch(url);
    if (!packageResponse.ok) throw new Error(`Offline package failed: ${url}`);
    const buffer = await packageResponse.arrayBuffer();
    await cache.put(url, new Response(buffer, {
      status: 200,
      headers: { 'Content-Type': packageResponse.headers.get('Content-Type') || 'application/octet-stream' },
    }));
  }
}

self.addEventListener('install', (event) => {
  event.waitUntil(precache().then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(caches.match(event.request, { ignoreVary: true }).then((cached) => {
    if (cached) return cached;
    return fetch(event.request).then((response) => {
      if (response.ok) caches.open(CACHE).then((cache) => cache.put(event.request, response.clone()));
      return response;
    }).catch(() => event.request.mode === 'navigate' ? caches.match('/index.html', { ignoreVary: true }) : Response.error());
  }));
});
