import datetime
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base
from config import ROLE_AGENT, ROLE_DELIVERY


class UserRole(enum.Enum):
    AGENT = ROLE_AGENT
    DELIVERY = ROLE_DELIVERY


class OrderStatus(enum.Enum):
    WAITING_DELIVERY = "Waiting Delivery"
    IN_DELIVERY = "In Delivery"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # Telegram user ID
    username = Column(String, unique=True, index=True, nullable=True)
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=True)
    is_authenticated = Column(Boolean, default=False)

    orders_created = relationship("Order", back_populates="agent", foreign_keys="Order.agent_id")
    orders_delivered = relationship("Order", back_populates="delivery_user", foreign_keys="Order.delivery_user_id")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    orders = relationship("Order", back_populates="product")


class Period(Base):
    __tablename__ = "periods"

    id = Column(Integer, primary_key=True, index=True)
    duration = Column(String, unique=True, index=True)  # e.g., '1 month', '3 months'

    orders = relationship("Order", back_populates="period")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    orders = relationship("Order", back_populates="payment_method")


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    orders = relationship("Order", back_populates="platform")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)  # Auto-generated order number like OrderN2892932
    agent_id = Column(Integer, ForeignKey("users.id"))
    delivery_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    period_id = Column(Integer, ForeignKey("periods.id"))
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    platform_id = Column(Integer, ForeignKey("platforms.id"))
    contact_info = Column(String)
    comments = Column(Text, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.WAITING_DELIVERY)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    delivery_started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    delivery_comments = Column(Text, nullable=True)

    agent = relationship("User", back_populates="orders_created", foreign_keys=[agent_id])
    delivery_user = relationship("User", back_populates="orders_delivered", foreign_keys=[delivery_user_id])
    product = relationship("Product", back_populates="orders")
    period = relationship("Period", back_populates="orders")
    payment_method = relationship("PaymentMethod", back_populates="orders")
    platform = relationship("Platform", back_populates="orders")
