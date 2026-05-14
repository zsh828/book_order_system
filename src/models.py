import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional


class Book:
    def __init__(self, isbn: str, title: str, author: str, price: float, stock: int, category: str):
        if not isbn or not isinstance(isbn, str):
            raise ValueError("ISBN cannot be empty")
        if price < 0:
            raise ValueError("Price cannot be negative")
        if stock < 0:
            raise ValueError("Stock cannot be negative")
        
        self.isbn = isbn
        self.title = title
        self.author = author
        self.price = price
        self.stock = stock
        self.category = category

    def to_dict(self) -> dict:
        return {
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "price": self.price,
            "stock": self.stock,
            "category": self.category
        }


class User:
    def __init__(self, user_id: str, username: str, email: str, password_hash: str, member_level: str = "normal", points: int = 0):
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")
        if member_level not in ["normal", "gold", "diamond"]:
            raise ValueError("Invalid member level")
        
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.member_level = member_level
        self.points = points

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def update_member_level(self):
        if self.points >= 5000:
            self.member_level = "diamond"
        elif self.points >= 1000:
            self.member_level = "gold"
        else:
            self.member_level = "normal"

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "member_level": self.member_level,
            "points": self.points
        }


class OrderItem:
    def __init__(self, isbn: str, quantity: int, unit_price: float):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")
            
        self.isbn = isbn
        self.quantity = quantity
        self.unit_price = unit_price

    def get_total(self) -> float:
        return self.quantity * self.unit_price

    def to_dict(self) -> dict:
        return {
            "isbn": self.isbn,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.get_total()
        }


class Order:
    def __init__(self, order_id: str, user_id: str, items: List[OrderItem], total_amount: float, discount_amount: float, status: str = "pending", created_at: Optional[datetime] = None):
        if status not in ["pending", "paid", "cancelled"]:
            raise ValueError("Invalid order status")
        if total_amount < 0:
            raise ValueError("Total amount cannot be negative")
        if discount_amount < 0:
            raise ValueError("Discount amount cannot be negative")

        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total_amount = total_amount
        self.discount_amount = discount_amount
        self.status = status
        self.created_at = created_at if created_at else datetime.now()

    def get_final_amount(self) -> float:
        return self.total_amount - self.discount_amount

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "total_amount": self.total_amount,
            "discount_amount": self.discount_amount,
            "final_amount": self.get_final_amount(),
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }