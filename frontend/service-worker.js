// ============================================================
// NEUROBUDDYY.AI — Service Worker v1
// Cache-first strategy for static assets.
// API calls (Firebase, /api/, Fast2SMS) are NEVER cached.
// ============================================================

const CACHE_NAME    = 'neurobuddyy-v1';
const CACHE_VERSION = '1.0.0';

// Static assets to pre-cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/images/neurobuddyy-logo.png',
  '/manifest.json'
];

// Patterns for requests that must ALWAYS go to the network (never cached)
const NETWORK_ONLY_PATTERNS = [
  '/api/',
  'firestore.googleapis.com',
  'firebase.googleapis.com',
  'googleapis.com',
  'gstatic.com',
  'fast2sms.com',
  'onrender.com',
  'peerjs.com'
];

// ── Install: pre-cache static assets ──────────────────────────
self.addEventListener('install', event => {
  console.log('[SW] Installing NEUROBUDDYY.AI Service Worker v1...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Pre-caching static assets...');
        // addAll will fail silently on individual errors (use add in loop for safety)
        return Promise.allSettled(
          STATIC_ASSETS.map(url => cache.add(url).catch(err => {
            console.warn(`[SW] Could not cache ${url}:`, err);
          }))
        );
      })
      .then(() => {
        console.log('[SW] Pre-caching complete. Taking control immediately.');
        return self.skipWaiting();
      })
  );
});

// ── Activate: delete old caches ───────────────────────────────
self.addEventListener('activate', event => {
  console.log('[SW] Activating new Service Worker...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(name => name !== CACHE_NAME)
            .map(name => {
              console.log(`[SW] Deleting old cache: ${name}`);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Activated and controlling all clients.');
        return self.clients.claim();
      })
  );
});

// ── Fetch: cache-first for static, network-only for API ───────
self.addEventListener('fetch', event => {
  const url = event.request.url;

  // --- Network-only: never cache API, Firebase, or external services ---
  const isNetworkOnly = NETWORK_ONLY_PATTERNS.some(pattern => url.includes(pattern));
  if (isNetworkOnly) {
    // Just let it pass through to the network with no caching
    return;
  }

  // --- Non-GET requests: pass through to network ---
  if (event.request.method !== 'GET') {
    return;
  }

  // --- Cache-first strategy for static assets ---
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          // Served from cache — also update cache in background (stale-while-revalidate)
          const networkFetch = fetch(event.request)
            .then(networkResponse => {
              if (networkResponse && networkResponse.status === 200) {
                const cloned = networkResponse.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, cloned));
              }
              return networkResponse;
            })
            .catch(() => { /* offline — silently ignore */ });

          return cachedResponse;
        }

        // Not in cache — fetch from network and cache for next time
        return fetch(event.request)
          .then(networkResponse => {
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type === 'opaque') {
              return networkResponse;
            }
            const cloned = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, cloned));
            return networkResponse;
          })
          .catch(() => {
            // Offline fallback: try to return the main page from cache
            if (event.request.headers.get('accept')?.includes('text/html')) {
              return caches.match('/index.html');
            }
          });
      })
  );
});

// ── Background sync: retry failed emergency alerts when back online ──
self.addEventListener('sync', event => {
  if (event.tag === 'retry-emergency') {
    console.log('[SW] Background sync: retrying emergency alert...');
    // Notifications only — actual retry is handled by the main page JS
  }
});

console.log(`[SW] NEUROBUDDYY.AI Service Worker v${CACHE_VERSION} loaded.`);
