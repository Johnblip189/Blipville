// Offline support: keep the app files cached so Blipville: On the Go works without internet.
const CACHE = "blipville-go-v81";
const FILES = ["./", "index.html", "style.css?v=57", "app.js?v=57", "countdown.js?v=57", "data.js?v=57", "manifest.webmanifest",
               "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png",
               "offline.html", "icons/server-down.png", "icons/maintenance.png"];
self.addEventListener("install", (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener("activate", (e) => e.waitUntil(
  caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
// Network first (so updates show up), falling back to the cache when offline or when the server is having trouble.
const fallback = (req) => caches.match(req).then((hit) =>
  // can't reach the server and this page isn't saved yet: show the "Blipville is napping" screen
  hit || (req.mode === "navigate" ? caches.match("offline.html") : Response.error()));
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  if (e.request.url.includes("status.json")) return;              // the maintenance switch: always ask GitHub, never cache
  e.respondWith(fetch(e.request).then((res) => {
    if (!res.ok) return res.status >= 500 ? fallback(e.request) : res;   // never save an error page over a good copy
    const copy = res.clone();
    caches.open(CACHE).then((c) => c.put(e.request, copy));
    return res;
  }).catch(() => fallback(e.request)));
});
