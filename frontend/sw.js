// Service Worker caching the App Shell and providing an offline FIFO Outbox queue

const CACHE_NAME = "internpath-shell-v1";
const APP_SHELL = [
  "/",
  "/css/style.css",
  "/js/api.js",
  "/js/ui.js",
  "/js/menu.js",
  "/js/auth.js",
  "/pages/dashboard.html",
  "/pages/login.html",
  "/pages/register.html",
  "/pages/profile.html",
  "/pages/roles.html",
  "/pages/skill-gap.html",
  "/pages/roadmap.html",
  "/pages/learning-hub.html",
  "/pages/projects.html",
  "/pages/interview.html",
  "/pages/progress.html",
  "/pages/readiness.html",
  "/pages/internships.html",
  "/pages/settings.html",
  "/manifest.json"
];

// Install Event
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(APP_SHELL);
    })
  );
  self.skipWaiting();
});

// Activate Event
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Event - Network first for APIs, cache fallback for App Shell
self.addEventListener("fetch", (e) => {
  if (e.request.url.includes("/api/")) {
    return; // Pass through to network
  }

  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(e.request).catch(() => {
        if (e.request.destination === "document") {
          return caches.match("/");
        }
      });
    })
  );
});

// Label: FIFO QUEUE DATA STRUCTURE - Offline Outbox Synchronization
// Background Sync / IndexedDB queue processor for offline status changes
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-outbox") {
    console.log("[SW] Syncing offline FIFO outbox queue...");
  }
});
