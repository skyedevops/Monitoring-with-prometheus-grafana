#!/bin/bash
# Script to verify that all microservices are running and healthy

set -e

SERVICES=(
  "user-service:5000"
  "order-service:5001"
  "payment-service:5002"
  "notification-service:5003"
)

echo "Verifying microservices..."

for service in "${SERVICES[@]}"; do
  NAME=${service%%:*}
  PORT=${service##*:}
  
  echo "Checking $NAME on port $PORT..."
  
  # Check health endpoint
  HEALTH_RESPONSE=$(curl -s -w "%{http_code}" "http://localhost:$PORT/health" -o /dev/null || echo "000")
  if [ "$HEALTH_RESPONSE" -ne 200 ]; then
    echo "❌ $NAME health check failed with status $HEALTH_RESPONSE"
    exit 1
  fi
  
  # Check metrics endpoint
  METRICS_RESPONSE=$(curl -s -w "%{http_code}" "http://localhost:$PORT/metrics" -o /dev/null || echo "000")
  if [ "$METRICS_RESPONSE" -ne 200 ]; then
    echo "❌ $NAME metrics check failed with status $METRICS_RESPONSE"
    exit 1
  fi
  
  echo "✅ $NAME is healthy"
done

echo "All services are healthy!"
exit 0