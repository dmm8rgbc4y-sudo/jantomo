// ======================================================
// 🧩 JANTOMO Service Worker
// キャッシュ管理（v1）
// ======================================================

const CACHE_NAME = "jantomo-cache-v1";
const urlsToCache = [
  "/", // トップページ
  "/static/css/style.css",
  "/static/js/schedule.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png"
];

// ------------------------------------
// インストール：キャッシュ登録
// ------------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[ServiceWorker] Caching app shell");
      return cache.addAll(urlsToCache);
    })
  );
});

// ------------------------------------
// フェッチ：キャッシュ優先で取得
// ------------------------------------
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});

// ------------------------------------
// アクティベート：古いキャッシュ削除
// ------------------------------------
self.addEventListener("activate", (event) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log("[ServiceWorker] Deleting old cache:", cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
