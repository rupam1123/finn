# Free temporary FINN review link

Prepared 3 November 2026. No hosted database, paid account or runtime migration is required. The app runs on this PC; the PC must remain awake and connected. This is temporary assessment sharing, not an always-on cloud deployment.

## Current readiness

Local HTTP checks passed for `/radar`, `/inbox`, `/universe`, `/research`, `/api/universe` and `/api/portfolio/overview` (HTTP 200). Capabilities report `public_review: true` and `research_jobs_enabled: false`. A research-job POST returned HTTP 403. These are local checks, not public-link or browser-layout verification.

The current app is already running at http://127.0.0.1:3000. No public tunnel was created: automatic approval review requires explicit approval to expose FINN's saved research and downloadable evidence through Cloudflare.

## Restart the app if it has stopped

Open PowerShell in `X:\finn_day1_verification_kit\finn` and run:

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --public-review --production --db data\finn.sqlite3
```

Keep this terminal running. Do not launch a second copy while ports 3000 and 8000 are already occupied. The existing production build is used. No model flag is needed.

## Proposed sharing action, pending explicit approval

After approval to share the saved research and evidence, the following command in a second PowerShell terminal creates a temporary public HTTPS URL:

```powershell
& 'C:\Program Files (x86)\cloudflared\cloudflared.exe' tunnel --no-autoupdate --url http://127.0.0.1:3000
```

Anyone with the generated `https://…trycloudflare.com` URL can browse the app's saved data and exposed evidence downloads. No email or other message is sent automatically. Read-only mode prevents new research jobs; it does not restrict who can read the shared app.

Before sharing, check the generated URL's `/radar`, `/research` and `/api/capabilities` routes, a saved evidence link, and verify research POSTs remain blocked. These public checks are still pending.

Press Ctrl+C in the tunnel terminal to stop sharing. Restarting the tunnel generates a different URL. Stopping the app, losing internet or allowing the PC to sleep also makes the link unavailable. Quick Tunnels have no uptime guarantee and do not support SSE; this saved-data read-only review does not start research jobs.

This sharing setup does not resolve the source, licensing, semantic or device-review gates recorded in the project handoff.

Official reference: [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
