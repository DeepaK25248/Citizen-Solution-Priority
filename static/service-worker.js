const CACHE_NAME = 'citysolution-shell-v13';
const SHELL_PATHS = [
  '/static/style.css?v=26',
  '/static/live.js?v=6',
  '/static/manifest.webmanifest',
  '/static/citysolution-icon.svg',
  '/static/offline.html'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(SHELL_PATHS);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (key) {
        return key.startsWith('citysolution-shell-') && key !== CACHE_NAME;
      }).map(function (key) {
        return caches.delete(key);
      }));
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', function (event) {
  const requestUrl = new URL(event.request.url);
  if (requestUrl.origin !== self.location.origin || event.request.method !== 'GET') return;

  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).catch(function () {
      return caches.match('/static/offline.html');
    }));
    return;
  }

  if (SHELL_PATHS.some(function (path) {
    return new URL(path, self.location.origin).pathname === requestUrl.pathname;
  })) {
    event.respondWith(caches.match(event.request).then(function (cached) {
      return cached || fetch(event.request);
    }));
  }
});