# Editor Shot List & Production Checklist
## *Monitoring with Prometheus, Grafana, Loki & Jaeger*

A practical checklist for cutting the master script into a finished video. Sections follow the script's timeline.

---

## Pre-Production

- [ ] Confirm Docker is installed; pre-build images once: `docker compose build`
- [ ] Pre-pull images so live recording isn't dominated by download time
- [ ] Seed `/var/log` with a few interesting entries (login attempts, kernel warnings) so the Loki panel has real data
- [ ] Generate baseline load: 200 requests to `user-service` over 60s so Prometheus has visible curves
- [ ] Open and pre-arrange the browser tabs you'll record:
  - `localhost:3000` (Grafana) — logged in
  - `localhost:9090/targets` (Prometheus)
  - `localhost:9090/alerts` (Prometheus alerts)
  - `localhost:16686` (Jaeger UI)
  - Terminal: `docker compose logs -f` in split view
- [ ] Set terminal font to a readable size (16pt+, high-contrast theme)
- [ ] Resize browser to 1440x900 or 1920x1080; hide bookmarks bar

---

## Shot-by-Shot Breakdown

### [0:00 – 0:45] Cold Open
- **Shot A1:** Screen recording — `docker compose up -d`, services streaming up
- **Shot A2:** Cut to Grafana dashboard auto-populating with metrics
- **Shot A3:** Cut to Loki Explore returning log lines
- **Audio:** Voiceover from script; music bed starts low
- **Overlay:** Title card "Building an Observability Stack from Scratch"

### [0:45 – 2:00] Intro & The Big Picture
- **Shot B1:** Architecture diagram (use the ASCII art from README, but render as a clean diagram in Excalidraw/draw.io)
- **Shot B2:** Logo lower-thirds for Prometheus, Loki, Jaeger, Grafana (first appearance only)

### [2:00 – 3:30] Project Layout
- **Shot C1:** `tree` command output of the repo (use `tree -L 2 --dirsfirst`)
- **Shot C2:** Highlight each top-level dir with a callout box as the voiceover names it

### [3:30 – 6:00] Microservices
- **Shot D1:** Open `Dockerfile` in VS Code, line-by-line zoom
  - Highlight `python:3.9-slim` (yellow box on first mention)
  - Highlight `COPY requirements.txt .` — "this is the magic line"
  - Highlight `gunicorn` CMD
- **Shot D2:** Open `app.py`, zoom to lines 2 and 7 (the Prometheus metrics import)
- **Shot D3:** Side-by-side: `prometheus_flask-exporter` code vs equivalent raw OpenTelemetry code (~10 lines) — show the boilerplate delta
- **Shot D4:** `curl localhost:5000/metrics | head -20` — show actual Prometheus output

### [6:00 – 8:30] Docker Compose Build Process
- **Shot E1:** Open `docker-compose.yml` in VS Code
- **Shot E2:** Spotlight the *absence* of `depends_on` — briefly show how adding it would break `docker compose up` if Prometheus is unhealthy (use a simulated test)
- **Shot E3:** Spotlight the bind-mount vs named-volume distinction with a split-screen callout
- **Shot E4:** Spotlight the duplicated CMD, then run `docker compose run user-service flask run --reload` to show why the override is there

### [8:30 – 11:30] Observability Stack
- **Shot F1:** `prometheus.yml` — zoom to `scrape_interval: 15s`
- **Shot F2:** Switch to `localhost:9090/targets` — show all 4 services `UP`
- **Shot F3:** `rules.yml` — zoom to `for: 1m` clauses, narrate hysteresis
- **Shot F4:** `loki/local-config.yaml` — zoom to `storage: filesystem` with a red warning overlay
- **Shot F5:** `promtail/config.yaml` + the `/var/log:/var/log:ro` mount — show system logs flowing into Loki

### [11:30 – 14:00] Grafana
- **Shot G1:** Show `observability/grafana/provisioning/` tree
- **Shot G2:** Delete the running Grafana container, restart it, show datasources and dashboards reappearing without clicking anything
- **Shot G3:** Live demo in Explore:
  - Prometheus query: `rate(http_requests_total[5m])` per service
  - Loki query: `{job="varlogs"} |= "error"`
  - Toggle time range from "Last 5m" to "Last 1h" — show the curves

### [14:00 – 16:00] Trade-offs Table
- **Shot H1:** Render the table as a full-screen graphic (use Canva/Figma), one row highlighted at a time as the VO covers it
- **Style:** Two columns side-by-side, "Demo" in green, "Production" in amber, with a small "→" arrow between them

### [16:00 – 17:15] Kubernetes
- **Shot I1:** `ls infrastructure/kubernetes/monitoring/` — show the 4 files
- **Shot I2:** Open one manifest, highlight the missing `resources:` and `volumeClaimTemplates:` with red boxes
- **Shot I3:** Show a screenshot of the kube-prometheus-stack Grafana dashboard list (~200 dashboards) — "this is what production looks like"

### [17:15 – 18:00] Outro
- **Shot J1:** Recap recap graphic with 4 numbered icons
- **Shot J2:** End card: repo URL, subscribe button, "Part 2: OpenTelemetry" tease

---

## Recording Quality Checks

- [ ] Audio: peak at -6dB, no clipping, room tone present
- [ ] No notification popups during recording (use Focus Assist / Do Not Disturb)
- [ ] Terminal cursor visible at readable size
- [ ] No cursor jitter — use a steady mouse or capture software that smooths
- [ ] All credentials redacted on-screen (already admin/admin, but call it out)
- [ ] `htop`/`docker stats` snapshots cleaned of personal paths

---

## Post-Production Pass

- [ ] Add chapter markers at every section header in the script
- [ ] Lower-thirds: name + role for any guest; otherwise skip
- [ ] Color-correct screen recordings (most are washed out — bump contrast +10)
- [ ] Add subtle sound effects on transitions (whoosh, blip) — keep them under -20dB
- [ ] Captions auto-generated, then corrected for "Prometheus" / "Loki" / "Gunicorn" spellings
- [ ] Pin a comment with the `docker compose up -d` command and the Grafana login
- [ ] Description includes:
  - Repo link
  - Timestamp to the trade-offs table
  - Links to Prometheus, Loki, Jaeger, Grafana docs
  - "Part 2" placeholder if planned

---

## Stretch Goals (If Time Allows)

- [ ] Add a 5-second "stack diagram" animation in the cold open (After Effects or Canva)
- [ ] Overlay a "live signal" indicator (pulsing dot) when Grafana is recording
- [ ] Cut a 30-second teaser for Shorts/Twitter: cold open + "subscribe" card
- [ ] Export a chapter-only audio version for the podcast crowd
