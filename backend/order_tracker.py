# This module contains the OrderTracker class, which encapsulates the core
# business logic for managing orders.

class OrderAlreadyExistsError(ValueError):
    """Raised when adding an order whose ID is already in storage."""


class OrderNotFoundError(ValueError):
    """Raised when an operation targets an order that does not exist."""


class OrderTracker:
    """
    Manages customer orders, providing functionalities to add, update,
    and retrieve order information.
    """
    VALID_STATUSES = frozenset(
        {"pending", "processing", "shipped", "delivered", "cancelled"}
    )

    def __init__(self, storage):
        required_methods = ['save_order', 'get_order', 'get_all_orders', 'delete_order']
        for method in required_methods:
            if not hasattr(storage, method) or not callable(getattr(storage, method)):
                raise TypeError(f"Storage object must implement a callable '{method}' method.")
        self.storage = storage

    def add_order(self, order_id: str, item_name: str, quantity: int, customer_id: str, status: str = "pending"):
        if not all(
            isinstance(value, str) and value.strip()
            for value in (order_id, item_name, customer_id)
        ):
            raise ValueError("Order ID, item name, and customer ID are required.")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        self._validate_status(status)

        if self.storage.get_order(order_id) is not None:
            raise OrderAlreadyExistsError(f"Order with ID '{order_id}' already exists.")

        order_data = {
            "order_id": order_id,
            "item_name": item_name,
            "quantity": quantity,
            "customer_id": customer_id,
            "status": status,
        }
        self.storage.save_order(order_id, order_data)
        return order_data

    def get_order_by_id(self, order_id: str):
        self._validate_order_id(order_id)
        return self.storage.get_order(order_id)

    def update_order_status(self, order_id: str, new_status: str):
        self._validate_order_id(order_id)
        self._validate_status(new_status)

        order = self.storage.get_order(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order with ID '{order_id}' does not exist.")

        updated_order = order.copy()
        updated_order["status"] = new_status
        self.storage.save_order(order_id, updated_order)
        return updated_order

    def delete_order(self, order_id: str):
        self._validate_order_id(order_id)
        order = self.storage.get_order(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order with ID '{order_id}' does not exist.")
        self.storage.delete_order(order_id)
        return order

    def list_orders(self, status: str = None, customer_id: str = None):
        """List orders, optionally filtered by status and/or customer ID."""
        if status is not None:
            self._validate_status(status)
        if customer_id is not None and (
            not isinstance(customer_id, str) or not customer_id.strip()
        ):
            raise ValueError("Customer ID must not be empty.")

        return [
            order
            for order in self.storage.get_all_orders().values()
            if (status is None or order.get("status") == status)
            and (customer_id is None or order.get("customer_id") == customer_id)
        ]

    def list_all_orders(self):
        return list(self.storage.get_all_orders().values())

    def list_orders_by_status(self, status: str):
        self._validate_status(status)
        return [
            order
            for order in self.storage.get_all_orders().values()
            if order.get("status") == status
        ]

    @staticmethod
    def _validate_order_id(order_id: str) -> None:
        if not isinstance(order_id, str) or not order_id.strip():
            raise ValueError("Order ID is required.")

    @classmethod
    def _validate_status(cls, status: str) -> None:
        if not isinstance(status, str) or status not in cls.VALID_STATUSES:
            raise ValueError(f"Invalid order status '{status}'.")
