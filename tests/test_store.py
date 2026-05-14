import pytest
from src.models import Book, User
from src.store import BookStore, UserManager, ShoppingCart, OrderManager


@pytest.fixture
def book_store():
    return BookStore()

@pytest.fixture
def user_manager():
    return UserManager()

@pytest.fixture
def order_manager(book_store, user_manager):
    return OrderManager(book_store, user_manager)

@pytest.fixture
def sample_book():
    return Book(isbn="ISBN001", title="Python Testing", author="Test Author", price=50.0, stock=10, category="Technology")

@pytest.fixture
def registered_user(user_manager):
    return user_manager.register("testuser", "test@example.com", "password123")


class TestBookStore:
    def test_add_book(self, book_store, sample_book):
        book_store.add_book(sample_book)
        assert book_store.get_book("ISBN001") == sample_book

    def test_add_duplicate_book_raises_error(self, book_store, sample_book):
        book_store.add_book(sample_book)
        with pytest.raises(ValueError, match="already exists"):
            book_store.add_book(sample_book)

    def test_search_books_by_title(self, book_store, sample_book):
        book_store.add_book(sample_book)
        results = book_store.search_books("Python")
        assert len(results) == 1
        assert results[0].isbn == "ISBN001"

    def test_search_books_no_match(self, book_store, sample_book):
        book_store.add_book(sample_book)
        results = book_store.search_books("Java")
        assert len(results) == 0

    def test_update_stock(self, book_store, sample_book):
        book_store.add_book(sample_book)
        book_store.update_stock("ISBN001", 20)
        assert book_store.get_book("ISBN001").stock == 20

    def test_update_stock_book_not_found_raises_error(self, book_store):
        with pytest.raises(ValueError, match="not found"):
            book_store.update_stock("INVALID", 10)

    def test_reduce_stock_success(self, book_store, sample_book):
        book_store.add_book(sample_book)
        book_store.reduce_stock("ISBN001", 5)
        assert book_store.get_book("ISBN001").stock == 5

    def test_reduce_stock_insufficient_raises_error(self, book_store, sample_book):
        book_store.add_book(sample_book)
        with pytest.raises(ValueError, match="Insufficient stock"):
            book_store.reduce_stock("ISBN001", 11)

    def test_restore_stock(self, book_store, sample_book):
        book_store.add_book(sample_book)
        book_store.reduce_stock("ISBN001", 5)
        book_store.restore_stock("ISBN001", 5)
        assert book_store.get_book("ISBN001").stock == 10


class TestUserManager:
    def test_register_user(self, user_manager):
        user = user_manager.register("newuser", "new@example.com", "pass")
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.member_level == "normal"

    def test_register_duplicate_email_raises_error(self, user_manager):
        user_manager.register("user1", "same@example.com", "pass1")
        with pytest.raises(ValueError, match="Email already registered"):
            user_manager.register("user2", "same@example.com", "pass2")

    def test_login_success(self, user_manager):
        user_manager.register("testuser", "test@example.com", "secret")
        user = user_manager.login("test@example.com", "secret")
        assert user.username == "testuser"

    def test_login_invalid_password_raises_error(self, user_manager):
        user_manager.register("testuser", "test@example.com", "secret")
        with pytest.raises(ValueError, match="Invalid email or password"):
            user_manager.login("test@example.com", "wrong")

    def test_login_nonexistent_email_raises_error(self, user_manager):
        with pytest.raises(ValueError, match="Invalid email or password"):
            user_manager.login("noone@example.com", "secret")


class TestShoppingCart:
    def test_add_item(self, book_store, sample_book):
        book_store.add_book(sample_book)
        cart = ShoppingCart("U0001", book_store)
        cart.add_item("ISBN001", 2)
        assert cart.get_items()["ISBN001"] == 2

    def test_add_item_book_not_found_raises_error(self, book_store):
        cart = ShoppingCart("U0001", book_store)
        with pytest.raises(ValueError, match="not found"):
            cart.add_item("INVALID", 1)

    def test_add_item_insufficient_stock_raises_error(self, book_store, sample_book):
        book_store.add_book(sample_book)
        cart = ShoppingCart("U0001", book_store)
        with pytest.raises(ValueError, match="Insufficient stock"):
            cart.add_item("ISBN001", 11)

    def test_remove_item(self, book_store, sample_book):
        book_store.add_book(sample_book)
        cart = ShoppingCart("U0001", book_store)
        cart.add_item("ISBN001", 1)
        cart.remove_item("ISBN001")
        assert "ISBN001" not in cart.get_items()

    def test_update_quantity(self, book_store, sample_book):
        book_store.add_book(sample_book)
        cart = ShoppingCart("U0001", book_store)
        cart.add_item("ISBN001", 1)
        cart.update_quantity("ISBN001", 5)
        assert cart.get_items()["ISBN001"] == 5

    def test_clear_cart(self, book_store, sample_book):
        book_store.add_book(sample_book)
        cart = ShoppingCart("U0001", book_store)
        cart.add_item("ISBN001", 1)
        cart.clear()
        assert cart.is_empty()


class TestOrderManager:
    def test_create_order_success(self, order_manager, sample_book, registered_user):
        order_manager.book_store.add_book(sample_book)
        cart = order_manager.get_cart(registered_user.user_id)
        cart.add_item("ISBN001", 2)
        
        order = order_manager.create_order(registered_user.user_id)
        
        assert order.status == "pending"
        assert order.total_amount == 100.0  # 2 * 50.0
        assert order.discount_amount == 0.0  # normal member
        assert order_manager.book_store.get_book("ISBN001").stock == 8
        assert cart.is_empty()

    def test_create_order_gold_member_discount(self, order_manager, sample_book, user_manager):
        order_manager.book_store.add_book(sample_book)
        user = user_manager.register("golduser", "gold@example.com", "pass")
        user.points = 1000
        user.update_member_level()
        assert user.member_level == "gold"
        
        cart = order_manager.get_cart(user.user_id)
        cart.add_item("ISBN001", 2)
        
        order = order_manager.create_order(user.user_id)
        
        assert order.total_amount == 100.0
        assert order.discount_amount == 5.0  # 5% of 100

    def test_create_order_diamond_member_discount(self, order_manager, sample_book, user_manager):
        order_manager.book_store.add_book(sample_book)
        user = user_manager.register("diamonduser", "diamond@example.com", "pass")
        user.points = 5000
        user.update_member_level()
        assert user.member_level == "diamond"
        
        cart = order_manager.get_cart(user.user_id)
        cart.add_item("ISBN001", 2)
        
        order = order_manager.create_order(user.user_id)
        
        assert order.total_amount == 100.0
        assert order.discount_amount == 10.0  # 10% of 100

    def test_create_order_empty_cart_raises_error(self, order_manager, registered_user):
        with pytest.raises(ValueError, match="Cart is empty"):
            order_manager.create_order(registered_user.user_id)

    def test_pay_order_success(self, order_manager, sample_book, registered_user):
        order_manager.book_store.add_book(sample_book)
        cart = order_manager.get_cart(registered_user.user_id)
        cart.add_item("ISBN001", 1)
        order = order_manager.create_order(registered_user.user_id)
        
        initial_points = registered_user.points
        order_manager.pay_order(order.order_id)
        
        assert order.status == "paid"
        assert registered_user.points == initial_points + 50  # 50.0 final amount

    def test_pay_order_already_paid_raises_error(self, order_manager, sample_book, registered_user):
        order_manager.book_store.add_book(sample_book)
        cart = order_manager.get_cart(registered_user.user_id)
        cart.add_item("ISBN001", 1)
        order = order_manager.create_order(registered_user.user_id)
        order_manager.pay_order(order.order_id)
        
        with pytest.raises(ValueError, match="cannot pay"):
            order_manager.pay_order(order.order_id)

    def test_cancel_order_success(self, order_manager, sample_book, registered_user):
        order_manager.book_store.add_book(sample_book)
        cart = order_manager.get_cart(registered_user.user_id)
        cart.add_item("ISBN001", 2)
        order = order_manager.create_order(registered_user.user_id)
        
        order_manager.cancel_order(order.order_id)
        
        assert order.status == "cancelled"
        assert order_manager.book_store.get_book("ISBN001").stock == 10  # Restored

    def test_cancel_paid_order_raises_error(self, order_manager, sample_book, registered_user):
        order_manager.book_store.add_book(sample_book)
        cart = order_manager.get_cart(registered_user.user_id)
        cart.add_item("ISBN001", 1)
        order = order_manager.create_order(registered_user.user_id)
        order_manager.pay_order(order.order_id)
        
        with pytest.raises(ValueError, match="Cannot cancel paid order"):
            order_manager.cancel_order(order.order_id)

    def test_sales_statistics(self, order_manager, sample_book, registered_user):
        order_manager.book_store.add_book(sample_book)
        cart = order_manager.get_cart(registered_user.user_id)
        cart.add_item("ISBN001", 3)
        order = order_manager.create_order(registered_user.user_id)
        order_manager.pay_order(order.order_id)
        
        stats = order_manager.get_sales_statistics()
        
        assert len(stats) == 1
        assert stats[0]["isbn"] == "ISBN001"
        assert stats[0]["sales_quantity"] == 3

    def test_sales_statistics_filtered_by_category(self, order_manager, sample_book, registered_user):
        book2 = Book(isbn="ISBN002", title="Novel", author="Writer", price=20.0, stock=5, category="Fiction")
        order_manager.book_store.add_book(sample_book)
        order_manager.book_store.add_book(book2)
        
        cart = order_manager.get_cart(registered_user.user_id)
        cart.add_item("ISBN001", 2)
        cart.add_item("ISBN002", 1)
        order = order_manager.create_order(registered_user.user_id)
        order_manager.pay_order(order.order_id)
        
        tech_stats = order_manager.get_sales_statistics(category="Technology")
        assert len(tech_stats) == 1
        assert tech_stats[0]["isbn"] == "ISBN001"
        
        fiction_stats = order_manager.get_sales_statistics(category="Fiction")
        assert len(fiction_stats) == 1
        assert fiction_stats[0]["isbn"] == "ISBN002"