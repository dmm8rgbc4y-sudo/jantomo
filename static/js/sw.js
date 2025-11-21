// ======================================================
// 🧩 JANTOMO Service Worker
// 安定動作用（v3）
// ======================================================

const CACHE_NAME = "jantomo-cache-v3";

// 静的リソースのみキャッシュ対象
const STATIC_ASSETS = [
  "/static/css/style.css",
  "/static/js/schedule.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png"
];

// -------------------------------------------
// インストール：静的リソースをキャッシュ
// -------------------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[ServiceWorker] Caching static assets");
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// -------------------------------------------
// アクティベート：古いキャッシュ削除
// -------------------------------------------
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

// -------------------------------------------
// フェッチ：状態依存ページはネット優先
// -------------------------------------------
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // 状態依存ページ（除外対象）
  const STATE_SENSITIVE_PATHS = ["/", "/register", "/friend"];

  if (
    STATE_SENSITIVE_PATHS.includes(url.pathname) ||
    url.pathname.startsWith("/api")
  ) {
    event.respondWith(fetch(event.request));
    return;
  }

  // キャッシュ対応
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // リダイレクトはキャッシュしない
        if (response.redirected) {
          console.log(
            "[ServiceWorker] Skipping cache for redirected response:",
            url.pathname
          );
          return fetch(response.url);
        }

        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
