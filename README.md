# Render reachability test

A throwaway page to check whether a free Render web service is reachable from Russian networks
inside Telegram — including files larger than 16 KB (some networks reportedly cut connections to
certain foreign hosts after ~16 KB).

- `/` — test page: shows whether it runs inside Telegram, whether telegram.org's script loaded,
  and downloads 300 KB of random bytes, reporting size and time.
- `/big` — the 300 KB payload. `/health` — status.

No dependencies, no database, no user data stored. Logs contain only the request line and status.

Run locally: `python3 server.py` → http://localhost:10000
