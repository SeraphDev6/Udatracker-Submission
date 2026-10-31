# Udatracker

An order tracker with a framework-agnostic `OrderTracker` (business logic), a Flask REST API, and a small frontend. Run it from this directory with `python -m backend.app`, and run the tests with `pytest`. Data is stored in memory only and is lost on restart.

> On macOS, port 5000 is often taken by AirPlay Receiver. Disable it, or run `python -c "from backend.app import app; app.run(port=5001)"`.

## Reflection

- **Design decision:** All validation and business rules live in `OrderTracker`; the routes only parse input, call it, and map results to HTTP codes. I added `OrderAlreadyExistsError` and `OrderNotFoundError` (subclasses of `ValueError`) so routes can return 409/404 without parsing error messages, and `add_order` now returns the created order.
- **Testing insight:** Writing the tests first showed that "fail fast" rules (invalid status or quantity must not touch storage) are easy to verify with a mock via `assert_not_called()`, and they pinned down the validation order.
- **Next step:** Add persistent storage (e.g. SQLite) behind the same storage interface (`save_order`, `get_order`, `get_all_orders`, `delete_order`), plus stricter validation such as maximum field lengths.

## API reference

Valid statuses: `pending`, `processing`, `shipped`, `delivered`, `cancelled`. Errors are always JSON: `{"error": "message"}`.

| Method & path | Body | Success | Errors |
|---|---|---|---|
| `POST /api/orders` | `order_id`, `item_name`, `quantity`, `customer_id`, optional `status` | `201` + order | `400` invalid input, `409` duplicate ID |
| `GET /api/orders/<order_id>` | – | `200` + order | `404` |
| `PUT /api/orders/<order_id>/status` | `{"new_status": "..."}` | `200` + updated order | `400` invalid status, `404` |
| `DELETE /api/orders/<order_id>` | – | `204` | `404` |
| `GET /api/orders` | – | `200` + list; optional `?status=` and `?customer_id=` filters (combinable) | `400` empty/invalid filter |

```
curl -X POST http://127.0.0.1:5000/api/orders -H "Content-Type: application/json" \
     -d '{"order_id": "CURL001", "item_name": "Headphones", "quantity": 1, "customer_id": "CUST123"}'
curl http://127.0.0.1:5000/api/orders/CURL001
curl -X PUT http://127.0.0.1:5000/api/orders/CURL001/status -H "Content-Type: application/json" \
     -d '{"new_status": "shipped"}'
curl "http://127.0.0.1:5000/api/orders?customer_id=CUST123&status=shipped"
curl -X DELETE http://127.0.0.1:5000/api/orders/CURL001
```

## Docker

```
docker compose up --build     # app at http://127.0.0.1:8080
```

## Project structure

```
.
├── backend
│   ├── __init__.py
│   ├── app.py
│   ├── in_memory_storage.py
│   ├── order_tracker.py
│   ├── requirements.txt
│   └── tests
│       ├── __init__.py
│       ├── test_api.py
│       └── test_order_tracker.py
├── frontend
│   ├── css
│   │   └── style.css
│   ├── index.html
│   └── js
│       └── script.js
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── README.md
```
