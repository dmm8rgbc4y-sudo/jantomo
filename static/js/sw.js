// ======================================================
// 🧩 JANTOMO Service Worker
// 安定動作用（v2）
// ======================================================

const CACHE_NAME = "jantomo-cache-v2";

// 静的リソースのみキャッシュ対象（状態依存ページは除外）
const STATIC_ASSETS = [
  "/static/css/style.css",
  "/static/js/schedule.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png"
];

// -------------------------------
// インストール：静的リソースをキャッシュ
// -------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[ServiceWorker] Caching static assets");
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// -------------------------------
// アクティベート：古いキャッシュ削除
// -------------------------------
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

// -------------------------------
// フェッチ：状態依存ページは毎回サーバーへ
// -------------------------------
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // 状態依存ページやAPIはキャッシュせず常にネットワークへ
  const STATE_SENSITIVE_PATHS = ["/", "/register", "/weekly", "/friend"];
  if (
    STATE_SENSITIVE_PATHS.includes(url.pathname) ||
    url.pathname.startsWith("/api")
  ) {
    event.respondWith(fetch(event.request));
    return;
  }

  // リダイレクト応答はキャッシュしない
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.redirected) {
          console.log("[ServiceWorker] Skipping cache for redirected response:", url.pathname);
          return fetch(response.url);
        }
        // 静的リソースはキャッシュに保存
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      })
      .catch(() => caches.match(event.request)) // オフライン時はキャッシュから
  );
});
