from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import random
import time

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Custom metrics
USER_CREATED = metrics.counter(
    'user_created_total', 'Number of users created', 
    labels={'status': lambda r: 'success' if r.status_code < 400 else 'error'}
)

USER_LOGIN = metrics.counter(
    'user_login_total', 'Number of user login attempts',
    labels={'status': lambda r: 'success' if r.status_code < 400 else 'error'}
)

# In-memory storage for demo
users = {}

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/users', methods=['POST'])
@USER_CREATED
def create_user():
    data = request.get_json()
    user_id = str(len(users) + 1)
    user = {
        'id': user_id,
        'username': data.get('username'),
        'email': data.get('email'),
        'created_at': time.time()
    }
    users[user_id] = user
    return jsonify(user), 201

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = users.get(user_id)
    if user:
        return jsonify(user), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/login', methods=['POST'])
@USER_LOGIN
def login():
    data = request.get_json()
    # Simulate authentication
    if random.random() > 0.1:  # 90% success rate
        return jsonify({'token': 'fake-jwt-token', 'user_id': '123'}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)