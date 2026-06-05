# Build Process Video Script
## *Monitoring with Prometheus, Grafana, Loki & Jaeger*

**Target runtime:** ~18 minutes
**Audience:** Intermediate developers / SRE-curious engineers who know Docker basics but want to understand *why* this stack is shaped the way it is.

---

## [0:00 – 0:45] COLD OPEN

**[B-ROLL: Terminal scrolling `docker compose up`, services coming up one by one, Grafana dashboard lighting up]**

> "If you've ever been paged at 3 AM because a service went down and you had *no idea why* — this video is for you. Today we're going to build, from scratch, a complete observability stack: four Flask microservices, instrumented end-to-end with Prometheus for metrics, Loki for logs, Jaeger for traces, and Grafana as the single pane of glass. But more importantly, I'm going to walk you through every design decision I made, and the trade-offs I'd accept differently in production."

---

## [0:45 – 2:00] INTRO & THE BIG PICTURE

**[SHOW: High-level architecture diagram from README]**

> "Before we write a single line of config, let's zoom out. Observability is built on three pillars: **metrics**, **logs**, and **traces**. Each one answers a different question.
>
> - **Metrics** answer: *Is something wrong, and by how much?* Think CPU usage, request rate, error rate.
> - **Logs** answer: *What happened, in detail?* Discrete events with full context.
> - **Traces** answer: *Where in the request path did the time go?* A single user request flowing across services.
>
> Most stacks fail because they pick **one** pillar and call it done. We're not going to do that. We pick one tool per pillar, and they're designed to compose:
> - **Prometheus** scrapes `/metrics` endpoints every 15 seconds.
> - **Loki** ingests logs pushed by **Promtail** — the same agent pattern as Prometheus, but for log streams.
> - **Jaeger** collects spans via its client libraries or OTLP.
> - **Grafana** queries all three and unifies them under one UI.
>
> **Trade-off I want to call out right now:** I could have used the **Elastic Stack** (Elasticsearch + Fluentd + Kibana) for logs, or the **Grafana Agent** instead of Promtail. I picked Loki because it shares the same label model as Prometheus, so you query logs with the *same mental model* as metrics. That's a huge DX win. The cost is that Loki is weaker for full-text search — it's optimized for grep-style queries, not Google-style search. For a learning/demo stack, that's the right call."

---

## [2:00 – 3:30] PROJECT LAYOUT

**[SHOW: Tree of the repo]**

> "Here's how the repo is laid out, and this is itself a design decision:
>
> ```
> ├── microservices/         # the apps we're observing
> │   ├── user-service/
> │   ├── order-service/
> │   ├── payment-service/
> │   └── notification-service/
> ├── observability/         # everything that watches the apps
> │   ├── prometheus/
> │   ├── grafana/
> │   ├── loki/
> │   └── promtail/
> ├── infrastructure/        # non-compose deploys (k8s manifests live here)
> ├── ci-cd/                 # verification scripts
> └── docker-compose.yml     # the one command that brings it all up
> ```
>
> **Why this split?** The boundary between *what you ship* (microservices) and *how you watch it* (observability) is enforced by the directory structure. If you're a developer touching the user service, you never have to know how Promtail is configured. If you're an SRE tuning alert thresholds, you never have to read Flask code.
>
> **Trade-off:** I considered one flat directory with a `deploy/` and `observe/` namespace, but four separate microservices each with their own Dockerfile is *much* easier to scale — adding a fifth service is `mkdir` and copy-paste, not refactoring a monorepo."

---

## [3:30 – 6:00] SECTION 1: THE MICROSERVICES

**[SHOW: `microservices/user-service/Dockerfile`]**

> "Let's start with the apps. The Dockerfile is intentionally minimal:
>
> ```dockerfile
> FROM python:3.9-slim
> WORKDIR /app
> COPY requirements.txt .
> RUN pip install --no-cache-dir -r requirements.txt
> COPY app.py .
> EXPOSE 5000
> CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
> ```
>
> **Three deliberate choices here:**
>
> **1. `python:3.9-slim` instead of `python:3.9`.** The full image is ~900MB; slim is ~150MB. For a demo, that matters — `docker compose up` finishes in seconds, not minutes. In production, I'd go further: use `python:3.9-alpine` (~50MB) or a `distroless` image. *But* Alpine uses musl libc, and some Python wheels — including gevent-based ones — break on it. Slim is the sweet spot.
>
> **2. `COPY requirements.txt` *before* `COPY app.py`.** This is **layer caching** at work. If I change `app.py` 50 times, the `pip install` layer is reused. If I had a single `COPY . .`, every code change re-runs `pip install`, and your build goes from 2 seconds to 40 seconds. This one line saves real time across a developer's day.
>
> **3. Gunicorn in CMD, not Flask's dev server.** Flask's built-in server is single-threaded, prints stacktraces to the user, and is documented as 'don't use this in production.' Gunicorn gives us a real WSGI server. The same CMD is repeated in `docker-compose.yml` — and that's intentional, I'll explain in a second."

**[SHOW: `microservices/user-service/app.py`]**

> "Now the Flask app itself. Look at line 2 and 7:
>
> ```python
> from prometheus_flask_exporter import PrometheusMetrics
> metrics = PrometheusMetrics(app)
> ```
>
> **One import. That's it.** That single line:
> - Adds a `/metrics` endpoint serving Prometheus-format text.
> - Wraps every route with a default request counter and latency histogram.
> - Lets me define custom metrics with the `@USER_CREATED` decorator.
>
> **Trade-off:** I considered **OpenTelemetry** instrumentation instead. OTel is the future — vendor-neutral, supports traces natively, and is what CNCF recommends. But for a *metrics-first* demo, `prometheus_flask_exporter` is one dependency and zero boilerplate. OTel would have meant an OTel collector, exporters, and more YAML. Right tool for the scope.
>
> **Another small but important choice:** the `login` route returns a 401 10% of the time — `random.random() > 0.1`. This is **chaos injected on purpose.** When we look at Grafana later, you'll see real error rates, not a perfect 200-only stream. A demo that always works teaches you nothing about debugging."

---

## [6:00 – 8:30] SECTION 2: THE BUILD PROCESS — DOCKER COMPOSE

**[SHOW: `docker-compose.yml`]**

> "This is the heart of the build process. One file, one command, ten services. Let's walk through the *non-obvious* bits.
>
> **First: there's no `depends_on` between services and the observability stack.** Look closely:
>
> ```yaml
> user-service:
>   build: ./microservices/user-service
>   command: gunicorn --bind 0.0.0.0:5000 app:app
> ```
>
> The microservices don't declare that they depend on Prometheus. **Why?** Because observability is *eventual* — if Prometheus is down for 30 seconds, the user service should still serve traffic. The scrape will just miss a window. If I had added `depends_on: [prometheus]`, `docker compose up` would refuse to start the user service when Prometheus was crashing — and now the user service is *also* down, defeating the point.
>
> **Trade-off:** A startup ordering like `depends_on` would guarantee the *first* scrape finds a healthy service. In K8s I'd use init containers or readiness probes. In Compose for local dev, the resilience model is more important than the cold-start ordering.
>
> **Second: bind mounts for code, named volume for state.**
>
> ```yaml
> volumes:
>   - ./microservices/user-service:/app   # bind mount - live code
>   prometheus_data:/prometheus            # named volume - persistent data
> ```
>
> Bind-mounting the source directory means **hot reload for free.** I edit `app.py`, restart, see changes. No rebuild. The Prometheus named volume means **metrics survive a `docker compose down`**. Without it, every restart wipes your time-series history and your Grafana dashboards go blank. Different lifecycles deserve different mount types.
>
> **Third: the `command:` override in compose duplicates the Dockerfile's CMD.**
>
> The Dockerfile says `CMD ["gunicorn", ...]`. The compose file says `command: gunicorn --bind 0.0.0.0:5000 app:app`. They look identical, but they're not — and that's on purpose. The Dockerfile CMD is what runs in CI or in `docker run` without compose. The compose override is what runs in dev. Later, I might want `command: flask run --reload` for local dev without rebuilding the image. Compose's `command` lets me do that without touching the Dockerfile.
>
> **Fourth: pinned versions on critical services, `latest` on stable ones.**
>
> ```yaml
> image: grafana/loki:2.5.0     # pinned
> image: prom/prometheus:latest # floating
> ```
>
> Loki at 2.5.0 because Loki's storage config schema has changed in past releases and 2.5.0's defaults match my `local-config.yaml`. Prometheus at `latest` because the scrape config is API-stable. **In production I'd pin everything** — `latest` is a future bug report. For a learning stack, `latest` saves you from running an ancient Grafana."

---

## [8:30 – 11:30] SECTION 3: THE OBSERVABILITY STACK

**[SHOW: `observability/prometheus/prometheus.yml`]**

> "Now the actual observability tools. Prometheus is the one most people get wrong, so let's be careful.
>
> **Pull, not push.** I have Prometheus scraping the services, not services pushing to Prometheus. This is the opposite of how logs work (where Promtail *pushes* to Loki). Why the difference?
>
> - **Pull** lets Prometheus be the source of truth for *what's running.* If a service disappears, Prometheus notices on the next scrape and marks it `up == 0`. If we used push, a dead service would just... stop pushing, and you'd need a separate health check.
> - **Pull** makes service discovery trivial. The config is just a list of hostnames.
> - **Pull** scales naturally — a service can't accidentally DDoS the metrics backend.
>
> **The cost:** pull requires the service to be reachable from Prometheus. In K8s that means a sidecar or service mesh. In serverless, you basically can't do it — that's why AWS CloudWatch is push-based. Right tool, right environment.
>
> **Scrape interval of 15 seconds.** That's Prometheus's default, and it's a deliberate choice. Faster — 5 seconds — doubles your storage and load for marginal freshness gains in most use cases. Slower — 60 seconds — means an outage can go unnoticed for almost a minute. **15s is the industry consensus sweet spot.**"

**[SHOW: `observability/prometheus/rules.yml`]**

> "Prometheus alone is a time-series database. The value comes from **alerting rules.** I defined two groups:
>
> - `service-alerts` — `ServiceDown`, `HighErrorRate`, `HighLatency`. These are the ones that wake you up.
> - `infrastructure-alerts` — `InstanceDown`, `HighCPUUsage`, `HighMemoryUsage`.
>
> Notice the `for:` clauses — `for: 1m`, `for: 2m`, `for: 5m`. **This is the difference between an alert and a notification.** A 1-second CPU spike isn't a problem; a 5-minute sustained spike is. The `for:` clause is hysteresis. **Trade-off:** it means your minimum detection latency is `scrape_interval + for_duration` — 15s + 1m = 75s for a ServiceDown. If you need sub-second alerting, Prometheus isn't the right tool. You'd want something stream-based like Grafana Mimir with shorter windows, or a push-based system."

**[SHOW: `observability/loki/local-config.yaml`]**

> "Loki. I want to highlight one config block:
>
> ```yaml
> common:
>   storage:
>     filesystem:
>       chunks_directory: /tmp/loki/chunks
> ```
>
> **Filesystem storage.** That's fine for a demo. **In production, this is a non-starter.** Loki is designed for object storage — S3, GCS, Azure Blob. On a local filesystem, you get one node, no replication, and the data dies with the container. I called this out explicitly in the README's Kubernetes section because it's the most common foot-gun.
>
> **The schema_config block is also pinned to `from: 2020-10-24`.** Loki's schema has evolved — v11, v12, v13 — and a newer Loki reading an older schema file will fail. Pinning the `from` date makes the config deterministic."

**[SHOW: `observability/promtail/config.yaml`]**

> "Promtail is Loki's log shipper. Look at the `__path__`:
>
> ```yaml
> __path__: /var/log/*log
> ```
>
> And in `docker-compose.yml`:
>
> ```yaml
> volumes:
>   - /var/log:/var/log:ro
> ```
>
> I'm mounting the **host's** `/var/log` into Promtail. **Trade-off:** this collects system logs (syslog, auth.log, kern.log) but **not** application logs from the Flask services — those write to stdout, which Docker captures in `docker logs`, not to a file. To collect those, I'd either (a) configure gunicorn to write to a log file inside the container and mount it, or (b) use a Docker logging driver. For this demo, system logs are enough to prove Loki works."

---

## [11:30 – 14:00] SECTION 4: GRAFANA AS THE UNIFIER

**[SHOW: `observability/grafana/provisioning/`]**

> "The single most underused feature in this stack is **Grafana provisioning.** Look at the directory:
>
> ```
> observability/grafana/provisioning/
> ├── datasources/    # auto-adds Prometheus & Loki datasources
> └── dashboards/     # auto-loads dashboard JSON files
> ```
>
> When Grafana starts, it reads these YAML files and **configures itself.** Datasources appear, dashboards appear, no clicking through the UI. **This is the entire reason a 12-factor app is reproducible.** If you configure Grafana by hand in the UI, your setup is captured in a SQLite database (`grafana.db`) that nobody can diff. If you configure via provisioning, it's all YAML in git.
>
> **Trade-off:** the provisioned config is *overlaid* on the database, not the only source of truth. If you edit a provisioned datasource in the UI, your change is silently overwritten on next container restart. This trips people up. The discipline is: **UI for exploration, YAML for production.**"

**[SHOW: Grafana UI live]**

> "Now let's see what we actually get. I'm going to log into Grafana — admin/admin, change that in production — and open Explore.
>
> [CLICK: Explore > Prometheus]
> Query: `rate(http_requests_total[5m])`
>
> **There it is.** Live request rate from the user service, scraped by Prometheus, rendered by Grafana. This is the loop closed.
>
> [CLICK: Explore > Loki]
> Query: `{job="varlogs"}`
>
> **And there are the system logs.** Same UI, different datasource, same query language. That's the design payoff."

---

## [14:00 – 16:00] SECTION 5: TRADE-OFFS I WOULD FLIP FOR PRODUCTION

> "Let me consolidate the trade-offs I made, because this is the most important part of the video for me. **Every decision in this stack has a production alternative, and you should know which is which.**
>
> | Decision | Demo choice | Production choice | Why it matters |
> |---|---|---|---|
> | Storage | Filesystem (Loki) | S3/GCS + replication | Durability and scale |
> | Service discovery | Static hostnames | Consul/K8s API | Services come and go |
> | Image tags | `latest` on most | Pinned digests | Reproducible deploys |
> | Auth | Admin/admin in env var | OAuth/SSO via Grafana | Defense in depth |
> | TLS | None | mTLS or reverse proxy | Encrypted in transit |
> | Resource limits | None | CPU/mem limits on every container | Prevents noisy neighbors |
> | Persistence | 1 prometheus volume | Managed Prometheus or Thanos/Mimir | Long-term retention |
> | Tracing | Jaeger all-in-one | Jaeger collector + query separated | Query load ≠ ingest load |
> | Alert routing | Alertmanager default | PagerDuty/Slack webhooks wired | Alerts that reach humans |
> | Microservice framework | Flask | FastAPI or gRPC | Async, type safety, throughput |
>
> **The pattern:** everything that's *easy in dev* and *unsafe in prod* is a tradeoff. I optimized for *learnability* — you can stand this up in 5 minutes and immediately see real data flowing. A production stack optimized for *operability* would take a week to provision and require a team to maintain."

---

## [16:00 – 17:15] SECTION 6: WHAT'S NEXT — KUBERNETES

**[SHOW: `infrastructure/kubernetes/monitoring/`]**

> "I deliberately did not make Kubernetes the primary deploy target, and I want to explain why.
>
> The `infrastructure/kubernetes/monitoring/` directory has the manifests for namespace, Loki ConfigMap, Loki Deployment, Prometheus ConfigMap. **But it's intentionally incomplete.** No PersistentVolumes, no ServiceMonitors, no resource limits, no NetworkPolicies.
>
> **Why include it at all?** Because the most common question after seeing this stack is 'how do I run it in K8s?' and the answer shouldn't be 'rewrite everything.' The manifests show the **migration path** — you can lift the configs from `observability/` into ConfigMaps, change `localhost` to K8s service names, and you're 70% of the way there.
>
> **The honest truth:** for a real production cluster, you'd use the **kube-prometheus-stack** Helm chart (which gives you Prometheus, Alertmanager, Grafana, and 200+ pre-built dashboards) and the **Grafana Loki Helm chart**. Rolling your own is an exercise, not a deliverable."

---

## [17:15 – 18:00] OUTRO

> "Recap of the build process:
> 1. **Four Flask services**, each with a one-line Prometheus exporter.
> 2. **Docker Compose** orchestrates everything with a single config file.
> 3. **Three observability tools**, one per pillar, all queryable from **Grafana**.
> 4. **Configuration as code** in `observability/` — no clicking, no hidden state.
>
> The big takeaway isn't *this specific stack* — it's the *pattern*. Pick one tool per pillar. Pin your versions. Make config declarative. Treat observability as a first-class artifact, not an afterthought.
>
> Links to the repo, the docker-compose file, and the Prometheus alerting rules are in the description. If you want a Part 2 where we add OpenTelemetry tracing across all four services and a service mesh — subscribe, that's next.
>
> Thanks for watching. Go instrument something."

**[END CARD: repo link, subscribe button]**

---

## Production Notes for the Editor

- **B-roll needed:** Grafana dashboard with three live panels (request rate, error rate, p95 latency); Loki Explore query returning syslog lines; Prometheus targets page showing all four services as `UP`.
- **Terminal commands to demo on-screen:**
  - `docker compose up -d`
  - `docker compose ps`
  - `curl http://localhost:5000/health`
  - `curl http://localhost:5000/metrics | head`
  - `./ci-cd/verify-services.sh`
- **Chapter markers (YouTube):** match the section headers above.
- **Music:** light, technical — break at section transitions.
- **Lower-thirds:** name each tool (Prometheus, Loki, Jaeger) the first time it appears on screen, with logo if possible.
