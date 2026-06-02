from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import random
import time

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Custom metrics
PAYMENTS_PROCESSED = metrics.counter(
    'payments_processed_total', 'Number of payments processed',
    labels={'status': lambda r: 'success' if r.status_code < 400 else 'error',
            'method': lambda r: r.args.get('method', 'unknown')}
)

PAYMENT_PROCESSING_TIME = metrics.histogram(
    'payment_processing_duration_seconds', 'Time spent processing payments',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

# Payment methods
PAYMENT_METHODS = ['credit_card', 'paypal', 'bank_transfer', 'crypto']

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/process', methods=['POST'])
def process_payment():
    start_time = time.time()
    
    data = request.get_json()
    amount = data.get('amount')
    method = data.get('method', random.choice(PAYMENT_METHODS))
    
    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    if method not in PAYMENT_METHODS:
        return jsonify({'error': 'Invalid payment method'}), 400
    
    # Simulate processing time based on method
    processing_times = {
        'credit_card': random.uniform(0.5, 2.0),
        'paypal': random.uniform(1.0, 3.0),
        'bank_transfer': random.uniform(2.0, 5.0),
        'crypto': random.uniform(0.1, 1.0)
    }
    
    time.sleep(processing_times[method])
    
    # Simulate occasional failures
    if random.random() < 0.05:  # 5% failure rate
        return jsonify({
            'error': 'Payment processing failed',
            'transaction_id': None
        }), 500
    
    # Successful payment
    transaction_id = f"txn_{int(time.time())}_{random.randint(1000, 9999)}"
    
    PAYMENTS_PROCESSED.labels(status='success', method=method).inc()
    PAYMENT_PROCESSING_TIME.observe(time.time() - start_time)
    
    return jsonify({
        'transaction_id': transaction_id,
        'amount': amount,
        'method': method,
        'status': 'completed',
        'timestamp': time.time()
    }), 200

@app.route('/refund', methods=['POST'])
def refund_payment():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    
    if not transaction_id:
        return jsonify({'error': 'Transaction ID required'}), 400
    
    # Simulate refund processing
    time.sleep(random.uniform(0.5, 2.0))
    
    if random.random() < 0.02:  # 2% failure rate for refunds
        return jsonify({
            'error': 'Refund processing failed',
            'refund_id': None
        }), 500
    
    refund_id = f"refund_{int(time.time())}_{random.randint(1000, 9999)}"
    
    return jsonify({
        'refund_id': refund_id,
        'transaction_id': transaction_id,
        'status': 'processed',
        'timestamp': time.time()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)