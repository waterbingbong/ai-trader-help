// AI Trading Assistant Service Worker
const CACHE_NAME = 'ai-trader-cache-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/assets/manifest.json',
  '/assets/icon-192x192.svg',
  '/assets/icon-512x512.svg',
  '/assets/styles.css',
  '/assets/responsive.css',
  '/assets/notification-handler.js',
  '/assets/app-loader.js',
  '/assets/_dash-component-suites/dash/dcc/async-graph.js',
  '/assets/_dash-component-suites/dash/dcc/async-dropdown.js',
  '/assets/_dash-component-suites/dash/dcc/async-slider.js'
];

// Dynamic cache for API responses and data
const DATA_CACHE_NAME = 'ai-trader-data-cache-v1';


// Install event - cache assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching app shell and static assets');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => {
        console.log('Service worker installed');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - implement stale-while-revalidate strategy for better offline experience
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // For API requests and data endpoints, use network-first strategy
  if (url.pathname.includes('_dash-update-component') || 
      url.pathname.includes('/api/') || 
      url.pathname.includes('data.json')) {
    
    event.respondWith(networkFirstStrategy(event.request));
  } 
  // For static assets, use cache-first strategy
  else {
    event.respondWith(cacheFirstStrategy(event.request));
  }
});

// Cache-first strategy for static assets
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    // Return cached response and update cache in background
    updateCache(request);
    return cachedResponse;
  }
  
  // If not in cache, fetch from network and cache
  return fetchAndCache(request, CACHE_NAME);
}

// Network-first strategy for API and data requests
async function networkFirstStrategy(request) {
  try {
    // Try network first
    const response = await fetchAndCache(request, DATA_CACHE_NAME);
    return response;
  } catch (error) {
    console.log('Network request failed, falling back to cache', error);
    
    // If network fails, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // If nothing in cache, return offline fallback
    if (request.headers.get('accept').includes('text/html')) {
      return caches.match('/offline.html');
    }
    
    // For data requests, return empty data
    if (request.url.includes('_dash-update-component')) {
      return new Response(JSON.stringify({
        'status': 'offline'
      }), {
        headers: {'Content-Type': 'application/json'}
      });
    }
    
    // Otherwise just propagate the error
    throw error;
  }
}

// Helper function to fetch and cache
async function fetchAndCache(request, cacheName) {
  const response = await fetch(request);
  
  // Check if valid response to cache
  if (response.ok && response.status === 200) {
    const responseToCache = response.clone();
    caches.open(cacheName).then(cache => {
      cache.put(request, responseToCache);
    });
  }
  
  return response;
}

// Helper function to update cache in background
function updateCache(request) {
  fetch(request).then(response => {
    if (response.ok && response.status === 200) {
      caches.open(CACHE_NAME).then(cache => {
        cache.put(request, response);
      });
    }
  }).catch(error => {
    console.log('Background cache update failed:', error);
  });
}

// Push notification event
self.addEventListener('push', (event) => {
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/assets/icon-192x192.svg',
    badge: '/assets/icon-192x192.svg',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/'
    },
    actions: [
      {
        action: 'view',
        title: 'View'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow(event.notification.data.url)
    );
  } else {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});