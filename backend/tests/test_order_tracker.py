import pytest
from unittest.mock import Mock
from ..order_tracker import OrderTracker

# --- Fixtures for Unit Tests ---

@pytest.fixture
def mock_storage():
    """
    Provides a mock storage object for tests.
    This mock will be configured to simulate various storage behaviors.
    """
    mock = Mock()
    # By default, mock get_order to return None (no order found)
    mock.get_order.return_value = None
    # By default, mock get_all_orders to return an empty dict
    mock.get_all_orders.return_value = {}
    return mock

@pytest.fixture
def order_tracker(mock_storage):
    """
    Provides an OrderTracker instance initialized with the mock_storage.
    """
    return OrderTracker(mock_storage)

def test_add_order_successfully(order_tracker, mock_storage):
    """Tests adding a new order with default 'pending' status."""
    order_tracker.add_order("ORD001", "Laptop", 1, "CUST001")

    mock_storage.save_order.assert_called_once_with(
        "ORD001",
        {
            "order_id": "ORD001",
            "item_name": "Laptop",
            "quantity": 1,
            "customer_id": "CUST001",
            "status": "pending",
        },
    )


def test_add_order_with_explicit_status(order_tracker, mock_storage):
    order_tracker.add_order("ORD001", "Laptop", 1, "CUST001", "processing")

    assert mock_storage.save_order.call_args.args[1]["status"] == "processing"


def test_add_order_raises_error_if_exists(order_tracker, mock_storage):
    mock_storage.get_order.return_value = {"order_id": "ORD_EXISTING"}

    with pytest.raises(
        ValueError, match="Order with ID 'ORD_EXISTING' already exists."
    ):
        order_tracker.add_order("ORD_EXISTING", "New Item", 1, "CUST001")

    mock_storage.save_order.assert_not_called()


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True, "2", None])
def test_add_order_rejects_invalid_quantity(order_tracker, mock_storage, quantity):
    with pytest.raises(ValueError, match="Quantity must be a positive integer."):
        order_tracker.add_order("ORD001", "Laptop", quantity, "CUST001")

    mock_storage.get_order.assert_not_called()
    mock_storage.save_order.assert_not_called()


@pytest.mark.parametrize(
    "field_values",
    [
        ("", "Laptop", 1, "CUST001"),
        ("ORD001", "", 1, "CUST001"),
        ("ORD001", "Laptop", 1, ""),
        (None, "Laptop", 1, "CUST001"),
        ("ORD001", None, 1, "CUST001"),
        ("ORD001", "Laptop", 1, None),
    ],
)
def test_add_order_rejects_missing_required_fields(order_tracker, field_values):
    with pytest.raises(ValueError, match="Order ID, item name, and customer ID are required."):
        order_tracker.add_order(*field_values)


def test_add_order_rejects_invalid_initial_status(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Invalid order status 'unknown'."):
        order_tracker.add_order("ORD001", "Laptop", 1, "CUST001", "unknown")

    mock_storage.get_order.assert_not_called()
    mock_storage.save_order.assert_not_called()


def test_get_existing_order_by_id(order_tracker, mock_storage):
    order = {"order_id": "ORD001", "status": "pending"}
    mock_storage.get_order.return_value = order

    assert order_tracker.get_order_by_id("ORD001") == order
    mock_storage.get_order.assert_called_once_with("ORD001")


def test_get_nonexistent_order_by_id_returns_none(order_tracker):
    assert order_tracker.get_order_by_id("MISSING") is None


def test_get_order_by_id_rejects_empty_id(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Order ID is required."):
        order_tracker.get_order_by_id("")

    mock_storage.get_order.assert_not_called()


def test_update_order_status_successfully(order_tracker, mock_storage):
    original_order = {"order_id": "ORD001", "status": "pending"}
    mock_storage.get_order.return_value = original_order

    updated = order_tracker.update_order_status("ORD001", "shipped")

    assert updated == {"order_id": "ORD001", "status": "shipped"}
    assert original_order["status"] == "pending"
    mock_storage.save_order.assert_called_once_with(
        "ORD001", {"order_id": "ORD001", "status": "shipped"}
    )


def test_update_order_status_rejects_invalid_status_before_read(
    order_tracker, mock_storage
):
    with pytest.raises(ValueError, match="Invalid order status 'unknown'."):
        order_tracker.update_order_status("ORD001", "unknown")

    mock_storage.get_order.assert_not_called()


def test_update_order_status_rejects_nonexistent_order(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Order with ID 'MISSING' does not exist."):
        order_tracker.update_order_status("MISSING", "shipped")

    mock_storage.save_order.assert_not_called()


def test_update_order_status_rejects_empty_id(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Order ID is required."):
        order_tracker.update_order_status("", "shipped")

    mock_storage.get_order.assert_not_called()


def test_list_all_orders_returns_empty_list_for_empty_storage(
    order_tracker,
):
    assert order_tracker.list_all_orders() == []


def test_list_all_orders_returns_order_values(order_tracker, mock_storage):
    orders = {
        "ORD001": {"order_id": "ORD001", "status": "pending"},
        "ORD002": {"order_id": "ORD002", "status": "shipped"},
    }
    mock_storage.get_all_orders.return_value = orders

    result = order_tracker.list_all_orders()

    assert len(result) == 2
    assert {order["order_id"] for order in result} == {"ORD001", "ORD002"}


def test_list_orders_by_status_returns_matching_orders(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {
        "ORD001": {"order_id": "ORD001", "status": "pending"},
        "ORD002": {"order_id": "ORD002", "status": "shipped"},
        "ORD003": {"order_id": "ORD003", "status": "pending"},
    }

    result = order_tracker.list_orders_by_status("pending")

    assert {order["order_id"] for order in result} == {"ORD001", "ORD003"}


def test_list_orders_by_status_returns_empty_list_when_no_orders_match(
    order_tracker, mock_storage
):
    mock_storage.get_all_orders.return_value = {
        "ORD001": {"order_id": "ORD001", "status": "pending"}
    }

    assert order_tracker.list_orders_by_status("shipped") == []


def test_list_orders_by_status_returns_empty_list_for_empty_storage(
    order_tracker,
):
    assert order_tracker.list_orders_by_status("pending") == []


@pytest.mark.parametrize("status", ["", "unknown", None, []])
def test_list_orders_by_status_rejects_invalid_status(
    order_tracker, mock_storage, status
):
    with pytest.raises(ValueError):
        order_tracker.list_orders_by_status(status)

    mock_storage.get_all_orders.assert_not_called()


def test_delete_order_removes_and_returns_order(order_tracker, mock_storage):
    order = {"order_id": "ORD001", "status": "pending"}
    mock_storage.get_order.return_value = order

    assert order_tracker.delete_order("ORD001") == order
    mock_storage.delete_order.assert_called_once_with("ORD001")


def test_delete_order_rejects_nonexistent_order(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Order with ID 'MISSING' does not exist."):
        order_tracker.delete_order("MISSING")

    mock_storage.delete_order.assert_not_called()


def test_delete_order_rejects_empty_id(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Order ID is required."):
        order_tracker.delete_order("")

    mock_storage.get_order.assert_not_called()


def test_list_orders_filters_by_customer_id(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {
        "ORD001": {"order_id": "ORD001", "customer_id": "C1", "status": "pending"},
        "ORD002": {"order_id": "ORD002", "customer_id": "C2", "status": "pending"},
    }

    result = order_tracker.list_orders(customer_id="C1")

    assert [order["order_id"] for order in result] == ["ORD001"]


def test_list_orders_combines_customer_and_status_filters(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {
        "ORD001": {"order_id": "ORD001", "customer_id": "C1", "status": "pending"},
        "ORD002": {"order_id": "ORD002", "customer_id": "C1", "status": "shipped"},
        "ORD003": {"order_id": "ORD003", "customer_id": "C2", "status": "pending"},
    }

    result = order_tracker.list_orders(customer_id="C1", status="pending")

    assert [order["order_id"] for order in result] == ["ORD001"]


def test_list_orders_rejects_empty_customer_id(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Customer ID must not be empty."):
        order_tracker.list_orders(customer_id="")

    mock_storage.get_all_orders.assert_not_called()


def test_tracker_requires_delete_order_on_storage():
    class Incomplete:
        def save_order(self): ...
        def get_order(self): ...
        def get_all_orders(self): ...

    with pytest.raises(TypeError, match="delete_order"):
        OrderTracker(Incomplete())
