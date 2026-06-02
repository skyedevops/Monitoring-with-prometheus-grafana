from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import random
import time
import threading

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Custom metrics
ORDERS_CREATED = metrics.counter(
    'orders_created_total', 'Number of orders created',
    labels={'status': lambda r: 'success' if r.status_code < 400 else 'error'}
)

ORDER_PROCESSING_TIME = metrics.histogram(
    'order_processing_duration_seconds', 'Time spent processing orders',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

# Background task to simulate async processing
def process_order_async(order_id):
    # Simulate processing time
    processing_time = random.uniform(0.5, 3.0)
    time.sleep(processing_time)
    # In a real system, this would update the order status
    print(f"Order {order_id} processed in {processing_time:.2f}s")

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/orders', methods=['POST'])
@ORDERS_CREATED
def create_order():
    start_time = time.time()
    
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not user_id or not product_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Simulate order creation
    order_id = str(random.randint(1000, 9999))
    order = {
        'id': order_id,
        'user_id': user_id,
        'product_id': product_id,
        'quantity': quantity,
        'status': 'created',
        'created_at': time.time()
    }
    
    # Start async processing
    thread = threading.Thread(target=process_order_async, args=(order_id,))
    thread.daemon = True
    thread.start()
    
    # Record processing time
    ORDER_PROCESSING_TIME.observe(time.time() - start_time)
    
    return jsonify(order), 201

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    # In a real system, this would fetch from a database
    # For demo, return a mock order
    return jsonify({
        'id': order_id,
        'user_id': '123',
        'product_id': 'product-456',
        'quantity': 2,
        'status': 'processed',
        'created_at': time.time() - 3600
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)