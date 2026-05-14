from typing import Dict, List, Optional
from src.models import Book, User, Order, OrderItem


class BookStore:
    def __init__(self):
        self.books: Dict[str, Book] = {}

    def add_book(self, book: Book):
        if book.isbn in self.books:
            raise ValueError(f"Book with ISBN {book.isbn} already exists")
        self.books[book.isbn] = book

    def get_book(self, isbn: str) -> Optional[Book]:
        return self.books.get(isbn)

    def search_books(self, keyword: str) -> List[Book]:
        keyword_lower = keyword.lower()
        results = []
        for book in self.books.values():
            if (keyword_lower in book.isbn.lower() or 
                keyword_lower in book.title.lower() or 
                keyword_lower in book.author.lower()):
                results.append(book)
        return results

    def update_stock(self, isbn: str, new_stock: int):
        if isbn not in self.books:
            raise ValueError(f"Book with ISBN {isbn} not found")
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
        self.books[isbn].stock = new_stock

    def reduce_stock(self, isbn: str, quantity: int):
        if isbn not in self.books:
            raise ValueError(f"Book with ISBN {isbn} not found")
        book = self.books[isbn]
        if book.stock < quantity:
            raise ValueError(f"Insufficient stock for book {isbn}. Available: {book.stock}, Requested: {quantity}")
        book.stock -= quantity

    def restore_stock(self, isbn: str, quantity: int):
        if isbn not in self.books:
            raise ValueError(f"Book with ISBN {isbn} not found")
        self.books[isbn].stock += quantity


class UserManager:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.next_id = 1

    def register(self, username: str, email: str, password: str) -> User:
        # Check if email already exists
        for u in self.users.values():
            if u.email == email:
                raise ValueError("Email already registered")
        
        user_id = f"U{self.next_id:04d}"
        self.next_id += 1
        password_hash = User.hash_password(password)
        user = User(user_id=user_id, username=username, email=email, password_hash=password_hash)
        self.users[user_id] = user
        return user

    def login(self, email: str, password: str) -> User:
        password_hash = User.hash_password(password)
        for user in self.users.values():
            if user.email == email and user.password_hash == password_hash:
                return user
        raise ValueError("Invalid email or password")

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def upgrade_member_level(self, user_id: str):
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        user.update_member_level()


class ShoppingCart:
    def __init__(self, user_id: str, book_store: BookStore):
        self.user_id = user_id
        self.book_store = book_store
        self.items: Dict[str, int] = {}  # isbn -> quantity

    def add_item(self, isbn: str, quantity: int):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        book = self.book_store.get_book(isbn)
        if not book:
            raise ValueError(f"Book with ISBN {isbn} not found")
        
        current_qty = self.items.get(isbn, 0)
        if book.stock < current_qty + quantity:
            raise ValueError(f"Insufficient stock for book {isbn}")
            
        self.items[isbn] = current_qty + quantity

    def remove_item(self, isbn: str):
        if isbn not in self.items:
            raise ValueError(f"Item {isbn} not in cart")
        del self.items[isbn]

    def update_quantity(self, isbn: str, quantity: int):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if isbn not in self.items:
            raise ValueError(f"Item {isbn} not in cart")
            
        book = self.book_store.get_book(isbn)
        if not book:
            raise ValueError(f"Book with ISBN {isbn} not found")
            
        if book.stock < quantity:
            raise ValueError(f"Insufficient stock for book {isbn}")
            
        self.items[isbn] = quantity

    def clear(self):
        self.items.clear()

    def get_items(self) -> Dict[str, int]:
        return self.items.copy()

    def is_empty(self) -> bool:
        return len(self.items) == 0


class OrderManager:
    def __init__(self, book_store: BookStore, user_manager: UserManager):
        self.book_store = book_store
        self.user_manager = user_manager
        self.orders: Dict[str, Order] = {}
        self.carts: Dict[str, ShoppingCart] = {}  # user_id -> ShoppingCart
        self.next_order_id = 1

    def get_cart(self, user_id: str) -> ShoppingCart:
        if user_id not in self.carts:
            self.carts[user_id] = ShoppingCart(user_id, self.book_store)
        return self.carts[user_id]

    def create_order(self, user_id: str) -> Order:
        user = self.user_manager.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        cart = self.get_cart(user_id)
        if cart.is_empty():
            raise ValueError("Cart is empty")
        
        items = []
        total_amount = 0.0
        
        # Validate stock and calculate total
        for isbn, quantity in cart.get_items().items():
            book = self.book_store.get_book(isbn)
            if not book:
                raise ValueError(f"Book {isbn} no longer exists")
            if book.stock < quantity:
                raise ValueError(f"Insufficient stock for book {isbn}")
            
            item = OrderItem(isbn=isbn, quantity=quantity, unit_price=book.price)
            items.append(item)
            total_amount += item.get_total()
        
        # Calculate discount
        discount_rate = 0.0
        if user.member_level == "gold":
            discount_rate = 0.05
        elif user.member_level == "diamond":
            discount_rate = 0.10
        
        discount_amount = total_amount * discount_rate
        
        # Deduct stock
        for item in items:
            self.book_store.reduce_stock(item.isbn, item.quantity)
        
        # Create order
        order_id = f"O{self.next_order_id:04d}"
        self.next_order_id += 1
        
        order = Order(
            order_id=order_id,
            user_id=user_id,
            items=items,
            total_amount=total_amount,
            discount_amount=discount_amount,
            status="pending"
        )
        self.orders[order_id] = order
        
        # Clear cart
        cart.clear()
        
        return order

    def pay_order(self, order_id: str):
        order = self.orders.get(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status != "pending":
            raise ValueError(f"Order status is {order.status}, cannot pay")
        
        order.status = "paid"
        
        # Add points to user
        user = self.user_manager.get_user(order.user_id)
        if user:
            final_amount = order.get_final_amount()
            user.points += int(final_amount)
            user.update_member_level()

    def cancel_order(self, order_id: str):
        order = self.orders.get(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status == "paid":
            raise ValueError("Cannot cancel paid order")
        
        if order.status == "cancelled":
            raise ValueError("Order already cancelled")
        
        # Restore stock
        for item in order.items:
            self.book_store.restore_stock(item.isbn, item.quantity)
        
        order.status = "cancelled"

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.orders.get(order_id)

    def get_sales_statistics(self, category: Optional[str] = None) -> List[Dict]:
        sales_map: Dict[str, int] = {}  # isbn -> total quantity sold
        
        for order in self.orders.values():
            if order.status != "paid":
                continue
            
            for item in order.items:
                book = self.book_store.get_book(item.isbn)
                if not book:
                    continue
                
                if category and book.category != category:
                    continue
                
                if item.isbn in sales_map:
                    sales_map[item.isbn] += item.quantity
                else:
                    sales_map[item.isbn] = item.quantity
        
        # Convert to list of dicts with book info
        result = []
        for isbn, qty in sales_map.items():
            book = self.book_store.get_book(isbn)
            if book:
                result.append({
                    "isbn": isbn,
                    "title": book.title,
                    "author": book.author,
                    "category": book.category,
                    "sales_quantity": qty
                })
        
        # Sort by sales quantity descending
        result.sort(key=lambda x: x["sales_quantity"], reverse=True)
        return result