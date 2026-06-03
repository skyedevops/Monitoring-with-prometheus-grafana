# Observability Stack Setup Guide

## Overview
This document explains how to set up and access the observability stack for monitoring the microservices.

## Prerequisites
- Docker and Docker Compose installed
- Network access to pull Docker images (if not already cached)

## Services Overview
The microservices are instrumented with Prometheus metrics and expose them at:
- User Service: http://localhost:5000/metrics
- Order Service: http://localhost:5001/metrics
- Payment Service: http://localhost:5002/metrics
- Notification Service: http://localhost:5003/metrics

## Observability Stack Components
When network access is available, you can start the full observability stack:

1. **Prometheus** - Metrics collection and storage
2. **Grafana** - Visualization and dashboards
3. **Jaeger** - Distributed tracing
4. **Loki** - Log aggregation
5. **Promtail** - Log shipping agent
6. **Alertmanager** - Alerting and notifications

## Starting the Observability Stack
Run the following command to start all observability services:

```bash
docker compose up -d prometheus grafana jaeger loki promtail alertmanager
```

## Accessing the Services
Once the stack is running, you can access the services at:

- **Prometheus**: http://localhost:9090
  - View targets: http://localhost:9090/targets
  - Query metrics: http://localhost:9090/graph

- **Grafana**: http://localhost:3000
  - Default login: admin/admin
  - Add Prometheus as a data source (http://prometheus:9090)
  - Import dashboards for monitoring microservices

- **Jaeger UI**: http://localhost:16686
  - View traces from instrumented services

- **Loki**: http://localhost:3100
  - Query logs via Grafana or Loki API

## Configuration Files
The observability stack is configured in the `observability/` directory:

- `observability/prometheus/prometheus.yml` - Prometheus scraping configuration
- `observability/grafana/provisioning/` - Grafana provisioning (dashboards, datasources)
- `observability/loki/local-config.yaml` - Loki configuration
- `observability/promtail/config.yaml` - Promtail configuration
- `observability/alertmanager/config.yml` - Alertmanager configuration

## Sample Dashboards
You can create Grafana dashboards to monitor:
- Request rates and latency per service
- Error rates and failure percentages
- Resource usage (CPU, memory, disk, network)
- Business metrics (users created, orders processed, payments processed, notifications sent)

## Alerting Rules
Example alerting rules are defined in `observability/prometheus/rules.yml`:
- ServiceDown: Alert when a service is unresponsive
- HighErrorRate: Alert when error rate exceeds threshold
- HighLatency: Alert when latency exceeds threshold
- Infrastructure alerts (CPU, memory, disk usage)

## Next Steps
1. Start the observability stack when network access is available
2. Explore the pre-configured dashboards in Grafana
3. Create custom dashboards for your specific monitoring needs
4. Set up notification channels in Alertmanager (email, Slack, etc.)
5. Consider adding distributed tracing with OpenTelemetry for deeper insights

## Troubleshooting
If you encounter issues:
- Check container logs: `docker compose logs <service>`
- Verify port mappings: `docker compose port <service> <port>`
- Ensure services are healthy: `./ci-cd/verify-services.sh`