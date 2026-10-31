from flask import Flask, request, jsonify, send_from_directory
from backend.order_tracker import (
    OrderAlreadyExistsError,
    OrderNotFoundError,
    OrderTracker,
)
from backend.in_memory_storage import InMemoryStorage

app = Flask(__name__, static_folder='../frontend')
in_memory_storage = InMemoryStorage()
order_tracker = OrderTracker(in_memory_storage)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api/orders', methods=['POST'])
def add_order_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    try:
        order = order_tracker.add_order(
            data.get("order_id"),
            data.get("item_name"),
            data.get("quantity"),
            data.get("customer_id"),
            data.get("status", "pending"),
        )
    except OrderAlreadyExistsError as e:
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(order), 201

@app.route('/api/orders/<string:order_id>', methods=['GET'])
def get_order_api(order_id):
    try:
        order = order_tracker.get_order_by_id(order_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if order is None:
        return jsonify({"error": f"Order with ID '{order_id}' not found."}), 404
    return jsonify(order), 200

@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
def update_order_status_api(order_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "new_status" not in data:
        return jsonify({"error": "Request body must include 'new_status'."}), 400

    try:
        order = order_tracker.update_order_status(order_id, data["new_status"])
    except OrderNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(order), 200

@app.route('/api/orders/<string:order_id>', methods=['DELETE'])
def delete_order_api(order_id):
    try:
        order_tracker.delete_order(order_id)
    except OrderNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return "", 204

@app.route('/api/orders', methods=['GET'])
def list_orders_api():
    try:
        orders = order_tracker.list_orders(
            status=request.args.get("status"),
            customer_id=request.args.get("customer_id"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(orders), 200

@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Resource not found."}), 404

@app.errorhandler(405)
def method_not_allowed(_error):
    return jsonify({"error": "Method not allowed."}), 405

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
