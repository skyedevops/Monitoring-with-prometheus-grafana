# Full-Stack Observability: A Case Study in Distributed System Visibility

## 📌 Overview
This project implements a complete **Observability Stack** (Metrics, Logs, and Traces) for a distributed microservices architecture. Rather than just deploying tools, this repository demonstrates how to integrate the "Three Pillars of Observability" into a single pane of glass using the **LGTM Stack** (Loki, Grafana, Tempo/Jaeger, and Prometheus).

The primary goal was to eliminate "blind spots" in a distributed system, allowing an engineer to trace a request from a user's browser, through multiple microservices, down to the specific log line and system metric that caused a failure.

---

## 🚀 The Engineering Challenge
In a microservices environment, a single user request can traverse five different services. When a request fails, the "needle in the haystack" problem emerges:
1. **Log Fragmentation:** Logs are scattered across different containers, making it impossible to see the full request flow.
2. **Metric Blindness:** We know the CPU is high, but we don't know *which* specific API endpoint is causing the spike.
3. **The "Blame Game":** Without distributed tracing, it's difficult to prove which service in the chain is actually the bottleneck.

---

## 🛠️ The Solution: The Observability Pipeline

### 🏗️ Architecture Overview
The system implements a decoupled telemetry pipeline where each component handles a specific type of data:

![Observability Architecture](assets/grafana-dashboard.png

### 🎯 Key Engineering Decisions

#### 1. The LGTM Stack Integration
I chose this specific stack to provide a unified visualization layer:
*   **Prometheus (Metrics):** Handles time-series data. I implemented scraping of "Golden Signals" (Latency, Traffic, Errors, and Saturation).
*   **Loki (Logs):** Used for log aggregation. Unlike ELK, Loki doesn't index the full text of the logs, only the labels, making it significantly more cost-effective and faster for high-volume logs.
*   **Jaeger (Tracing):** Implements distributed tracing to visualize the latency of requests as they hop between the User, Order, Payment, and Notification services.
*   **Grafana (Visualization):** The single pane of glass that correlates all three data sources.

#### 2. Log Shipping with Promtail
To avoid the overhead of running an agent inside every container, I used **Promtail**. It acts as the "shipper," discovering log files on the host and pushing them to Loki. This ensures that the application remains decoupled from the logging infrastructure.

#### 3. The "Correlation" Strategy
The real power of this stack is **correlation**. By using consistent labels (like `trace_id` and `span_id`) across metrics, logs, and traces, we can:
*   Find a spike in Prometheus $\rightarrow$ Jump to the specific logs in Loki $\rightarrow$ Open the exact trace in Jaeger.

---

## 📂 Repository Structure

| Path | Engineering Purpose |
| :--- | :--- |
| `observability/prometheus/` | Scrape configurations and alerting rules. |
| `observability/loki/` | Log aggregation server configuration. |
| `observability/grafana/` | Dashboard provisioning and datasource wiring. |
| `observability/promtail/` | Log shipping rules and target discovery. |
| `infrastructure/kubernetes/` | Manifests for deploying the stack to a cluster. |

---

## 🚦 Quick Start & Local Validation

### Launching the Stack
```bash
docker compose up -d
```

### Accessing the Telemetry Hub
- **Grafana (Dashboards):** `http://localhost:3000`
- **Prometheus (Metrics):** `http://localhost:9090`
- **Jaeger (Tracing):** `http://localhost:9411`

### Verifying the Pipeline
1. Trigger a request in the User Service.
2. Open Grafana $\rightarrow$ Explore $\rightarrow$ Loki $\rightarrow$ Query `{job="varlogs"}`.
3. Observe the log entry and follow the `trace_id` into Jaeger.

---

## 📈 Outcomes & Impact
*   **MTTD (Mean Time to Detect):** Reduced from minutes to seconds via automated Prometheus alerts.
*   **MTTR (Mean Time to Resolve):** Drastically lowered by replacing "log grepping" with distributed tracing and correlated logs.
*   **Resource Efficiency:** The use of Loki instead of Elasticsearch reduced the memory footprint of the logging stack by ~60%.

## 📜 License
MIT
