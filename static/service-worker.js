// EFRIS PWA Service Worker
const CACHE_NAME = 'efris-v1.0.1';
const OFFLINE_URL = '/static/offline.html';

// Assets to cache on install
const ASSETS_TO_CACHE = [
  '/static/dashboard_multitenant.html',
  '/static/mobile_client.html',
  '/static/offline.html',
  '/static/manifest.json',
  // Add more critical assets as needed
];

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching critical assets');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => {
        console.log('[Service Worker] Installation complete');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[Service Worker] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[Service Worker] Activation complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip API calls (always use network for fresh data)
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .catch(() => {
          // Return offline indicator for failed API calls
          return new Response(
            JSON.stringify({ 
              error: 'Offline', 
              message: 'You are currently offline. Please check your connection.' 
            }),
            { 
              headers: { 'Content-Type': 'application/json' },
              status: 503
            }
          );
        })
    );
    return;
  }
  
  // Network-first strategy for HTML pages (to get latest version)
  if (request.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response and cache it
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // If network fails, serve from cache or offline page
          return caches.match(request)
            .then((cachedResponse) => {
              return cachedResponse || caches.match(OFFLINE_URL);
            });
        })
    );
    return;
  }
  
  // Cache-first strategy for static assets (CSS, JS, images)
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          // Return cached version and update cache in background
          fetch(request).then((response) => {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, response);
            });
          }).catch(() => {});
          return cachedResponse;
        }
        
        // Not in cache, fetch from network
        return fetch(request)
          .then((response) => {
            // Cache successful responses
            if (response && response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return response;
          });
      })
  );
});

// Background sync for offline invoice submissions
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);
  
  if (event.tag === 'sync-invoices') {
    event.waitUntil(
      syncOfflineInvoices()
    );
  }
});

// Push notifications for invoice updates
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received');
  
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'EFRIS Notification';
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: data.url || '/static/dashboard_multitenant.html',
    actions: [
      {
        action: 'open',
        title: 'Open',
        icon: '/static/icons/open-24x24.png'
      },
      {
        action: 'close',
        title: 'Dismiss',
        icon: '/static/icons/close-24x24.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'open') {
    const urlToOpen = event.notification.data;
    event.waitUntil(
      clients.openWindow(urlToOpen)
    );
  }
});

// Helper function to sync offline invoices
async function syncOfflineInvoices() {
  try {
    // Get offline invoices from IndexedDB or localStorage
    const offlineInvoices = await getOfflineInvoices();
    
    if (offlineInvoices.length === 0) {
      console.log('[Service Worker] No offline invoices to sync');
      return;
    }
    
    console.log(`[Service Worker] Syncing ${offlineInvoices.length} offline invoices`);
    
    // Submit each invoice
    for (const invoice of offlineInvoices) {
      try {
        const response = await fetch('/api/invoices/submit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': invoice.apiKey
          },
          body: JSON.stringify(invoice.data)
        });
        
        if (response.ok) {
          // Remove from offline storage
          await removeOfflineInvoice(invoice.id);
          console.log(`[Service Worker] Invoice ${invoice.id} synced successfully`);
        }
      } catch (error) {
        console.error(`[Service Worker] Failed to sync invoice ${invoice.id}:`, error);
      }
    }
  } catch (error) {
    console.error('[Service Worker] Sync failed:', error);
    throw error;
  }
}

// Placeholder functions (implement with IndexedDB in production)
async function getOfflineInvoices() {
  // TODO: Implement IndexedDB read
  return [];
}

async function removeOfflineInvoice(id) {
  // TODO: Implement IndexedDB delete
  console.log(`Removed invoice ${id} from offline storage`);
}

// Message handler for client communication
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    const urlsToCache = event.data.urls || [];
    event.waitUntil(
      caches.open(CACHE_NAME)
        .then((cache) => cache.addAll(urlsToCache))
    );
  }
});

console.log('[Service Worker] Loaded successfully');
