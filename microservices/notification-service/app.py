from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import random
import time

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Custom metrics
NOTIFICATIONS_SENT = metrics.counter(
    'notifications_sent_total', 'Number of notifications sent',
    labels={'type': lambda r: r.args.get('type', 'unknown'),
            'status': lambda r: 'success' if r.status_code < 400 else 'error'}
)

NOTIFICATION_PROCESSING_TIME = metrics.histogram(
    'notification_processing_duration_seconds', 'Time spent processing notifications',
    buckets=(0.05, 0.1, 0.5, 1.0, 2.0)
)

# Notification types
NOTIFICATION_TYPES = ['email', 'sms', 'push', 'slack']

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/send', methods=['POST'])
def send_notification():
    start_time = time.time()
    
    data = request.get_json()
    recipient = data.get('recipient')
    message = data.get('message')
    notif_type = data.get('type', random.choice(NOTIFICATION_TYPES))
    
    if not recipient or not message:
        return jsonify({'error': 'Recipient and message are required'}), 400
    
    if notif_type not in NOTIFICATION_TYPES:
        return jsonify({'error': 'Invalid notification type'}), 400
    
    # Simulate processing time based on type
    processing_times = {
        'email': random.uniform(0.1, 1.0),
        'sms': random.uniform(0.05, 0.5),
        'push': random.uniform(0.01, 0.2),
        'slack': random.uniform(0.1, 0.5)
    }
    
    time.sleep(processing_times[notif_type])
    
    # Simulate occasional failures
    if random.random() < 0.03:  # 3% failure rate
        NOTIFICATIONS_SENT.labels(type=notif_type, status='error').inc()
        return jsonify({
            'error': 'Notification delivery failed',
            'notification_id': None
        }), 500
    
    # Successful notification
    notification_id = f"notif_{int(time.time())}_{random.randint(1000, 9999)}"
    
    NOTIFICATIONS_SENT.labels(type=notif_type, status='success').inc()
    NOTIFICATION_PROCESSING_TIME.observe(time.time() - start_time)
    
    return jsonify({
        'notification_id': notification_id,
        'recipient': recipient,
        'type': notif_type,
        'message': message,
        'status': 'sent',
        'timestamp': time.time()
    }), 200

@app.route('/batch', methods=['POST'])
def send_batch_notification():
    start_time = time.time()
    
    data = request.get_json()
    recipients = data.get('recipients', [])
    message = data.get('message')
    notif_type = data.get('type', 'email')
    
    if not recipients or not message:
        return jsonify({'error': 'Recipients list and message are required'}), 400
    
    if not isinstance(recipients, list):
        return jsonify({'error': 'Recipients must be a list'}), 400
    
    # Send notifications to each recipient
    sent_count = 0
    failed_count = 0
    
    for recipient in recipients:
        # Simulate sending
        time.sleep(random.uniform(0.01, 0.1))
        
        if random.random() < 0.02:  # 2% failure rate per recipient
            failed_count += 1
        else:
            sent_count += 1
    
    NOTIFICATION_PROCESSING_TIME.observe(time.time() - start_time)
    
    return jsonify({
        'batch_id': f"batch_{int(time.time())}_{random.randint(1000, 9999)}",
        'total_recipients': len(recipients),
        'sent_count': sent_count,
        'failed_count': failed_count,
        'type': notif_type,
        'status': 'completed',
        'timestamp': time.time()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)