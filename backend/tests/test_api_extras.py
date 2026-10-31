import pytest
from backend.app import app, in_memory_storage


@pytest.fixture
def client():
    app.config['TESTING'] = True
    in_memory_storage.clear()
    with app.test_client() as client:
        yield client


def _create(client, order_id, customer_id="C1", status="pending"):
    return client.post('/api/orders', json={
        "order_id": order_id, "item_name": "Item", "quantity": 1,
        "customer_id": customer_id, "status": status,
    })


def test_add_order_duplicate_returns_409(client):
    _create(client, "DUP1")
    response = _create(client, "DUP1")
    assert response.status_code == 409
    assert "already exists" in response.json["error"]


def test_add_order_invalid_quantity_returns_400(client):
    response = client.post('/api/orders', json={
        "order_id": "BAD1", "item_name": "Item", "quantity": 0, "customer_id": "C1",
    })
    assert response.status_code == 400
    assert "error" in response.json


def test_add_order_without_json_returns_400(client):
    assert client.post('/api/orders', data="not json").status_code == 400


def test_update_status_invalid_returns_400(client):
    _create(client, "U1")
    response = client.put('/api/orders/U1/status', json={"new_status": "bogus"})
    assert response.status_code == 400


def test_update_status_missing_order_returns_404(client):
    response = client.put('/api/orders/NOPE/status', json={"new_status": "shipped"})
    assert response.status_code == 404


def test_update_status_missing_body_returns_400(client):
    _create(client, "U2")
    assert client.put('/api/orders/U2/status', json={}).status_code == 400


@pytest.mark.parametrize("query", ["status=", "status=bogus"])
def test_list_orders_invalid_status_returns_400(client, query):
    assert client.get(f'/api/orders?{query}').status_code == 400


def test_list_orders_filters_by_customer_id(client):
    _create(client, "A", customer_id="C1")
    _create(client, "B", customer_id="C2")
    response = client.get('/api/orders?customer_id=C1')
    assert response.status_code == 200
    assert [o["order_id"] for o in response.json] == ["A"]


def test_list_orders_combines_customer_and_status(client):
    _create(client, "A", customer_id="C1", status="pending")
    _create(client, "B", customer_id="C1", status="shipped")
    _create(client, "C", customer_id="C2", status="pending")
    response = client.get('/api/orders?customer_id=C1&status=pending')
    assert [o["order_id"] for o in response.json] == ["A"]


def test_list_orders_empty_customer_id_returns_400(client):
    assert client.get('/api/orders?customer_id=').status_code == 400


def test_delete_order_returns_204_and_removes_it(client):
    _create(client, "D1")
    assert client.delete('/api/orders/D1').status_code == 204
    assert client.get('/api/orders/D1').status_code == 404


def test_delete_missing_order_returns_404(client):
    response = client.delete('/api/orders/NOPE')
    assert response.status_code == 404
    assert "error" in response.json


def test_unknown_api_path_returns_json_404(client):
    response = client.get('/api/does-not-exist')
    assert response.status_code == 404
    assert response.is_json
    assert "error" in response.json


def test_wrong_method_returns_json_405(client):
    response = client.patch('/api/orders')
    assert response.status_code == 405
    assert response.is_json
