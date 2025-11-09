# TeamWatcher Feed (Self-Hosted)

Minimal FastAPI service that serves iCalendar (ICS) feeds for:
- Buffalo Bills (NFL) — ZIP-aware "how to watch" notes for NYC logic.
- UNC Men's Basketball — basic schedule with titles and alerts.

## Quick Start (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open: http://localhost:8000/ics/bills?zip=11218&subs=paramount,youtubetv  
Open: http://localhost:8000/ics/unc

### Subscribe from your phone (HTTPS)

Use a domain + HTTPS so iOS/Google accept the subscription easily. One easy self-host path is **Caddy**:

1) Point DNS `feed.yourdomain.com` → your server IP  
2) Install Caddy (macOS): `brew install caddy`  
3) `Caddyfile`:
```
feed.yourdomain.com {
  encode zstd gzip
  reverse_proxy 127.0.0.1:8000
}
```
4) Run API: `uvicorn app.main:app --host 127.0.0.1 --port 8000`  
5) Start Caddy: `sudo caddy run --config ./Caddyfile`

Caddy fetches a trusted TLS cert (Let's Encrypt).

## Files
- app/main.py — API endpoints
- app/ics_utils.py — ICS generator
- app/data_bills_2025.py — Remaining 2025 Bills schedule (best-known)
- app/data_unc_2025.py — Nov–Jan UNC MBB schedule (best-known)
- app/watch_rules.py — NYC watch guidance (simplified)
