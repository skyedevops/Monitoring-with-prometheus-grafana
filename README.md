# Monitoring with Prometheus, Grafana, Loki, and Jaeger

## Overview
This project provides a comprehensive observability stack for monitoring microservices using:
- **Prometheus** for metrics collection and storage
- **Grafana** for visualization and dashboarding
- **Loki** for log aggregation (like Prometheus, but for logs)
- **Promtail** for shipping logs to Loki
- **Jaeger** for distributed tracing
- **Alertmanager** for handling alerts

The stack monitors four simple Flask-based microservices:
- User Service (port 5000)
- Order Service (port 5001)
- Payment Service (port 5002)
- Notification Service (port 5003)

## Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   User Service  │    │  Order Service   │    │ Payment Service  │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬────────┘
          │                      │                       │
          ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Network (default)                    │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│  │Prometheus   │  │   Grafana    │  │    Loki      │  │Jaeger    │
│  │(metrics)    │  │(dashboards)  │  │(logs)        │  │(tracing) │
│  └─────┬───────┘  └───────┬──────┘  └───────┬──────┘  └────┬──────┘
│        │                  │                 │             │
│        ▼                  ▼                 ▼             ▼
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│  │Node Exporter│  │Alertmanager  │  │Promtail      │  │Services  │
│  │(host metrics)│  │(alerts)      │  │(log shipper)│  │(app logs)│
│  └─────────────┘  └──────────────┘  └──────────────┘  └──────────┘
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites
- Docker Engine (version 20.10+)
- Docker Compose (version 2.0+)
- Approximately 2GB of free disk space
- Ports 3000, 3100, 9090, 9093, 9411, 5000-5003 must be available

## Environment Variables
The following environment variables can be set in a `.env` file or exported before running:
| Variable | Description | Default |
|----------|-------------|---------|
| `GF_SECURITY_ADMIN_PASSWORD` | Grafana admin password | `admin` |
| `GF_USERS_ALLOW_SIGN_UP` | Allow user sign-up in Grafana | `false` |

## Build Process
This project uses Docker Compose to build and orchestrate all services. No manual compilation is required as all services use pre-built Docker images or Dockerfiles in their respective directories.

The build process consists of:
1. Building the four microservices from their respective Dockerfiles
2. Pulling pre-built images for observability components (Prometheus, Grafana, Loki, etc.)
3. Starting all services in the correct dependency order

## Configuration Files
Key configuration files in the repository:
- `docker-compose.yml` - Defines all services and their configuration
- `observability/prometheus/prometheus.yml` - Prometheus scraping configuration
- `observability/loki/local-config.yaml` - Loki server configuration
- `observability/promtail/config.yaml` - Promtail log shipping configuration
- `observability/grafana/provisioning/datasources/datasource.yml` - Grafana datasource provisioning (Prometheus)
- `observability/grafana/provisioning/datasources/loki-datasource.yml` - Grafana datasource provisioning (Loki)
- `observability/grafana/provisioning/dashboards/loki-dashboard.yml` - Grafana dashboard provisioning
- `observability/grafana/dashboards/loki-logs-dashboard.json` - Pre-built Loki logs dashboard

## Deployment Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Monitoring-with-prometheus-grafana
```

### 2. Start the Stack
```bash
docker compose up -d
```

### 3. Verify Services are Running
```bash
docker compose ps
```
You should see all services in the "Up" state.

### 4. Access the Interfaces
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger UI**: http://localhost:9411
- **Loki API**: http://localhost:3100 (no UI, but accessible via Grafana)

### 5. Explore Logs in Grafana
1. Login to Grafana at http://localhost:3000
2. Go to **Explore** (compass icon)
3. Select **Loki** as the data source
4. Try the query: `{job="varlogs"}` to see system logs
5. For service logs, you may need to configure your services to write to files (see below)

## What Each Service Does

### Microservices
- **User Service**: Handles user-related operations (Flask app on port 5000)
- **Order Service**: Manages order processing (Flask app on port 5001)
- **Payment Service**: Processes payments (Flask app on port 5002)
- **Notification Service**: Sends notifications (Flask app on port 5003)

### Observability Components
- **Prometheus**: Scrapes metrics from services and node exporter every 15s
- **Grafana**: Visualizes metrics and logs via dashboards
- **Loki**: Aggregates logs from Promtail and other sources
- **Promtail**: Ships logs from `/var/log/*log` and service logs to Loki
- **Jaeger**: Collects and visualizes distributed traces
- **Alertmanager**: Handles alerts sent by Prometheus

## Extending the Stack

### Adding Custom Metrics to Services
To expose metrics from your Flask services:
1. Install prometheus-flask-exporter: `pip install prometheus-flask-exporter`
2. Add to your app:
   ```python
   from prometheus_flask_exporter import PrometheusMetrics
   metrics = PrometheusMetrics(app)
   ```
3. Prometheus will automatically scrape metrics at `/metrics`

### Adding Log Collection for Services
1. Configure your service to write logs to a file (e.g., `/var/log/myapp.log`)
2. Add to `observability/promtail/config.yaml`:
   ```yaml
   - job_name: myservice
     static_configs:
       - targets: [localhost]
         labels:
           job: myservice
           __path__: /var/log/myapp.log
   ```
3. Restart Promtail: `docker compose restart promtail`

### Adding Custom Dashboards
1. Create a dashboard JSON file in `observability/grafana/dashboards/`
2. Add a reference to it in `observability/grafana/provisioning/dashboards/loki-dashboard.yml`
3. Restart Grafana: `docker compose restart grafana`

## Troubleshooting

### Common Issues and Solutions

#### 1. Loki Fails to Start (Config File Not Found)
**Symptom**: `failed parsing config: open /etc/loki/local-config.yaml: no such file or directory`
**Solution**:
- Ensure `observability/loki/local-config.yaml` exists
- Check that the volume mapping in docker-compose.yml is correct:
  ```yaml
  volumes:
    - ./observability/loki:/etc/loki
  ```
- Run: `ls -la observability/loki/` to verify the file exists

#### 2. Promtail Fails to Start (Config File Not Found)
**Symptom**: `Unable to parse config: open /etc/promtail/config.yml: no such file or directory`
**Solution**:
- Ensure `observability/promtail/config.yaml` exists
- Check volume mapping:
  ```yaml
  volumes:
    - ./observability/promtail:/etc/promtail
    - /var/log:/var/log:ro
  ```

#### 3. Grafana Cannot Connect to Loki
**Symptom**: In Grafana Explore, Loki datasource shows "Failed to resource call"
**Solution**:
- Verify Loki is accessible from Grafana container:
  ```bash
  docker compose exec grafana curl -s http://loki:3100/ready
  ```
  Should return "ready"
- Check that the Loki datasource URL in Grafana is set to `http://loki:3100`
- Ensure both services are on the same Docker network (they are by default)

#### 4. No Logs Appearing in Grafana
**Symptom**: Loki datasource works but no logs show up in Explore
**Solution**:
- Check Promtail is running: `docker compose ps promtail`
- Verify Promtail is reading logs:
  ```bash
  docker compose logs promtail | tail -20
  ```
  Look for lines like "Adding target" and "watching new directory"
- Verify Loki is receiving logs:
  ```bash
  docker compose logs loki | grep -i "received\|entry"
  ```
- Try a broader query in Grafana Explore: `{job!=""}` to see all logs

#### 5. Services Not Being Scraped by Prometheus
**Symptom**: Prometheus shows 0 targets for your services
**Solution**:
- Check that services are exposing metrics endpoint
- By default, these Flask apps don't expose metrics - you need to add prometheus_flask_exporter
- Verify service is reachable:
  ```bash
  docker compose exec prometheus curl -s http://user-service:5000/metrics
  ```
- If metrics endpoint doesn't exist, add the exporter to your service

#### 6. Port Conflicts
**Symptom**: Error when starting: "Bind for 0.0.0.0:3000 failed: port is already allocated"
**Solution**:
- Check what's using the port: `sudo lsof -i :3000`
- Either stop the conflicting service or change the port in docker-compose.yml

## Kubernetes Deployment

The `infrastructure/kubernetes/monitoring/` directory contains Kubernetes manifests for deploying the observability stack:

### Files:
- `namespace.yaml`: Creates the `monitoring` namespace
- `loki-configmap.yaml`: Loki configuration as a ConfigMap
- `loki-deployment.yaml`: Loki Deployment and Service
- `prometheus-configmap.yaml`: Prometheus configuration

### To Deploy:
```bash
kubectl apply -f infrastructure/kubernetes/monitoring/
```

### Notes:
1. The Kubernetes manifests are configured for a basic Loki deployment
2. For production use, you may want to:
   - Add persistence with PersistentVolumes
   - Configure proper storage (S3, GCS, etc.) for Loki
   - Add resource limits and requests
   - Configure alerting rules
   - Set up proper authentication and TLS

The Docker Compose setup in the root directory remains the primary method for local development and testing.

## Maintenance

### Viewing Logs
```bash
# View logs for a specific service
docker compose logs -f <service-name>

# Follow all logs
docker compose logs -f
```

### Stopping the Stack
```bash
docker compose down
```

### Removing All Data (Volumes)
```bash
docker compose down -v
```

### Updating Images
```bash
docker compose pull
docker compose up -d
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Inspired by the Grafana Loki documentation
- Based on the Prometheus and Grafana official Docker images
- Microservices adapted from common Flask tutorial patterns