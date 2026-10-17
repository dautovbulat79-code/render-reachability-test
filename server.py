"""Reachability test for hosting a Telegram Mini App.

Checks from a real phone/network whether this host can deliver more than a tiny page:
some Russian networks reportedly cut connections to certain foreign hosts after ~16 KB.

No dependencies, no storage, no user data. Logs only path, status and timing.
"""

import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAYLOAD_SIZE = 300 * 1024
PAYLOAD = os.urandom(PAYLOAD_SIZE)  # random bytes: proxies can't compress them below the 16 KB limit
STARTED = time.time()

PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Тест доступности</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
  :root { color-scheme: light; }
  body { margin: 0; padding: 20px 16px; background: #F6F0E4; color: #13203A;
         font: 16px/1.45 -apple-system, system-ui, "Segoe UI", sans-serif; }
  h1 { font-size: 22px; margin: 0 0 16px; }
  .row { background: #FFFCF6; border: 1px solid #E7DECF; border-radius: 16px;
         padding: 14px 16px; margin-bottom: 10px; }
  .label { font-size: 13px; color: #7A7468; }
  .value { font-size: 18px; font-weight: 700; margin-top: 2px; }
  button { width: 100%; min-height: 48px; border: 0; border-radius: 999px; background: #13203A;
           color: #FFFCF6; font-size: 16px; font-weight: 600; margin-top: 8px; }
  .hint { font-size: 13px; color: #7A7468; margin-top: 14px; }
</style>
</head>
<body>
<h1>Тест доступности хостинга</h1>
<div class="row"><div class="label">Страница</div><div class="value">✅ загрузилась</div></div>
<div class="row"><div class="label">Открыто внутри Telegram</div><div class="value" id="tg">…</div></div>
<div class="row"><div class="label">Скрипт Telegram (telegram.org)</div><div class="value" id="tgjs">…</div></div>
<div class="row"><div class="label">Большой файл (300 КБ)</div><div class="value" id="big">…</div></div>
<button id="again" type="button">Повторить тест</button>
<p class="hint">Сделайте скриншот этого экрана и отметьте сеть: мобильный интернет (оператор) или Wi-Fi, VPN вкл/выкл.</p>
<script>
  var wa = window.Telegram && window.Telegram.WebApp;
  document.getElementById("tgjs").textContent = wa ? "✅ загрузился" : "❌ не загрузился";
  // Only checks presence; initData is never sent anywhere.
  document.getElementById("tg").textContent = wa && wa.initData ? "✅ да" : "— нет (обычный браузер)";
  if (wa) { try { wa.ready(); wa.expand(); } catch (e) {} }

  function runBig() {
    var el = document.getElementById("big");
    el.textContent = "загружается…";
    var t0 = performance.now();
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, 30000);
    fetch("/big?t=" + Date.now(), { cache: "no-store", signal: ctrl.signal })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.arrayBuffer(); })
      .then(function (buf) {
        clearTimeout(timer);
        var s = ((performance.now() - t0) / 1000).toFixed(1);
        var ok = buf.byteLength === __SIZE__;
        el.textContent = (ok ? "✅ " : "❌ неполный: ") + Math.round(buf.byteLength / 1024) + " КБ за " + s + " с";
      })
      .catch(function (e) {
        clearTimeout(timer);
        el.textContent = "❌ ошибка: " + (e.name === "AbortError" ? "нет ответа 30 с" : e.message);
      });
  }
  document.getElementById("again").onclick = runBig;
  runBig();
</script>
</body>
</html>
""".replace("__SIZE__", str(PAYLOAD_SIZE))


class Handler(BaseHTTPRequestHandler):
    server_version = "reachability-test"
    sys_version = ""

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._send(200, "text/html; charset=utf-8", PAGE.encode())
        elif path == "/big":
            self._send(200, "application/octet-stream", PAYLOAD)
        elif path == "/health":
            self._send(200, "application/json", b'{"status":"ok","uptime_s":%d}' % int(time.time() - STARTED))
        else:
            self._send(404, "text/plain; charset=utf-8", b"not found")

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        # No IPs or headers in logs: just the request line and status.
        print(f"{self.log_date_time_string()} {args[0] if args else ''} -> {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))  # Render sets PORT
    print(f"Listening on 0.0.0.0:{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
