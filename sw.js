// Suivi de classe : fonctionnement hors ligne.
// Aucune donnée d'élève ne passe ici : elles restent dans le stockage de la tablette.
const CACHE = 'suivi-classe-v11';
const FILES = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable.png', './pdf.min.js', './pdf.worker.min.js'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// Réponse immédiate depuis le cache, mise à jour en arrière-plan quand le réseau est là.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(caches.open(CACHE).then(async cache => {
    const cached = await cache.match(e.request, {ignoreSearch: true});
    const noStore = new URL(e.request.url).search !== ''; // retour de connexion Microsoft (?code=…) : ne pas garder en cache
    const net = fetch(e.request).then(r => { if (r && r.ok && !noStore) cache.put(e.request, r.clone()); return r; }).catch(() => cached);
    return cached || net;
  }));
});
