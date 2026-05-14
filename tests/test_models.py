import pytest
from src.models import Book, User, Order, OrderItem


class TestBook:
    def test_create_valid_book(self):
        book = Book(isbn="123", title="Test", author="Author", price=10.0, stock=5, category="Fiction")
        assert book.isbn == "123"
        assert book.price == 10.0
        assert book.stock == 5

    def test_create_book_negative_price_raises_error(self):
        with pytest.raises(ValueError, match="Price cannot be negative"):
            Book(isbn="123", title="Test", author="Author", price=-1.0, stock=5, category="Fiction")

    def test_create_book_negative_stock_raises_error(self):
        with pytest.raises(ValueError, match="Stock cannot be negative"):
            Book(isbn="123", title="Test", author="Author", price=10.0, stock=-1, category="Fiction")

    def test_to_dict(self):
        book = Book(isbn="123", title="Test", author="Author", price=10.0, stock=5, category="Fiction")
        d = book.to_dict()
        assert d["isbn"] == "123"
        assert d["title"] == "Test"


class TestUser:
    def test_create_valid_user(self):
        user = User(user_id="U0001", username="testuser", email="test@example.com", password_hash="hash")
        assert user.user_id == "U0001"
        assert user.member_level == "normal"

    def test_create_user_invalid_email_raises_error(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            User(user_id="U0001", username="testuser", email="invalid-email", password_hash="hash")

    def test_create_user_invalid_member_level_raises_error(self):
        with pytest.raises(ValueError, match="Invalid member level"):
            User(user_id="U0001", username="testuser", email="test@example.com", password_hash="hash", member_level="platinum")

    def test_hash_password(self):
        h1 = User.hash_password("password123")
        h2 = User.hash_password("password123")
        h3 = User.hash_password("different")
        assert h1 == h2
        assert h1 != h3

    def test_update_member_level_to_gold(self):
        user = User(user_id="U0001", username="testuser", email="test@example.com", password_hash="hash", points=999)
        user.update_member_level()
        assert user.member_level == "normal"
        
        user.points = 1000
        user.update_member_level()
        assert user.member_level == "gold"

    def test_update_member_level_to_diamond(self):
        user = User(user_id="U0001", username="testuser", email="test@example.com", password_hash="hash", points=4999)
        user.update_member_level()
        assert user.member_level == "gold"
        
        user.points = 5000
        user.update_member_level()
        assert user.member_level == "diamond"


class TestOrderItem:
    def test_create_valid_item(self):
        item = OrderItem(isbn="123", quantity=2, unit_price=10.0)
        assert item.get_total() == 20.0

    def test_create_item_zero_quantity_raises_error(self):
        with pytest.raises(ValueError, match="Quantity must be positive"):
            OrderItem(isbn="123", quantity=0, unit_price=10.0)

    def test_create_item_negative_price_raises_error(self):
        with pytest.raises(ValueError, match="Unit price cannot be negative"):
            OrderItem(isbn="123", quantity=1, unit_price=-10.0)


class TestOrder:
    def test_create_valid_order(self):
        item = OrderItem(isbn="123", quantity=1, unit_price=10.0)
        order = Order(order_id="O0001", user_id="U0001", items=[item], total_amount=10.0, discount_amount=0.0)
        assert order.status == "pending"
        assert order.get_final_amount() == 10.0

    def test_get_final_amount_with_discount(self):
        item = OrderItem(isbn="123", quantity=1, unit_price=100.0)
        order = Order(order_id="O0001", user_id="U0001", items=[item], total_amount=100.0, discount_amount=10.0)
        assert order.get_final_amount() == 90.0

    def test_create_order_invalid_status_raises_error(self):
        item = OrderItem(isbn="123", quantity=1, unit_price=10.0)
        with pytest.raises(ValueError, match="Invalid order status"):
            Order(order_id="O0001", user_id="U0001", items=[item], total_amount=10.0, discount_amount=0.0, status="shipped")