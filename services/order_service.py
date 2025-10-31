import datetime
import random
import string

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from models import Order, Product, Period, PaymentMethod, Platform, User, OrderStatus

def generate_order_number():
    prefix = "OrderN"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{timestamp}{random_suffix}"

def create_order(
    db: Session,
    agent_id: int,
    product_name: str,
    period_duration: str,
    payment_method_name: str,
    platform_name: str,
    contact_info: str,
    comments: str | None = None,
):
    product = db.query(Product).filter(Product.name == product_name).first()
    period = db.query(Period).filter(Period.duration == period_duration).first()
    payment_method = db.query(PaymentMethod).filter(PaymentMethod.name == payment_method_name).first()
    platform = db.query(Platform).filter(Platform.name == platform_name).first()

    if not all([product, period, payment_method, platform]):
        raise ValueError("One or more required reference data (product, period, payment method, platform) not found.")

    order_id = generate_order_number()
    order = Order(
        id=order_id,
        agent_id=agent_id,
        product_id=product.id,
        period_id=period.id,
        payment_method_id=payment_method.id,
        platform_id=platform.id,
        contact_info=contact_info,
        comments=comments,
        status=OrderStatus.WAITING_DELIVERY,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

def get_order_by_id(db: Session, order_id: str):
    return db.query(Order).options(
        joinedload(Order.product),
        joinedload(Order.period),
        joinedload(Order.payment_method),
        joinedload(Order.platform)
    ).filter(Order.id == order_id).first()

def get_all_orders(db: Session):
    return db.query(Order).order_by(desc(Order.created_at)).all()

def get_orders_by_status(db: Session, status: OrderStatus):
    return db.query(Order).filter(Order.status == status).order_by(desc(Order.created_at)).all()

def update_order_status(
    db: Session,
    order_id: str,
    new_status: OrderStatus,
    delivery_user_id: int | None = None,
    delivery_comments: str | None = None,
):
    order = get_order_by_id(db, order_id)
    if order:
        order.status = new_status
        if new_status == OrderStatus.IN_DELIVERY and delivery_user_id:
            order.delivery_user_id = delivery_user_id
            order.delivery_started_at = datetime.datetime.utcnow()
        elif new_status == OrderStatus.COMPLETED:
            order.completed_at = datetime.datetime.utcnow()
            order.delivery_comments = delivery_comments
        db.commit()
        db.refresh(order)
    return order

def assign_delivery_user(db: Session, order_id: str, delivery_user_id: int):
    order = get_order_by_id(db, order_id)
    if order:
        order.delivery_user_id = delivery_user_id
        order.delivery_started_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(order)
    return order

def get_orders_for_delivery_user(db: Session, delivery_user_id: int):
    return (
        db.query(Order)
        .filter(
            Order.delivery_user_id == delivery_user_id,
            Order.status.in_([OrderStatus.WAITING_DELIVERY, OrderStatus.IN_DELIVERY]),
        )
        .order_by(desc(Order.created_at))
        .all()
    )

def get_delivery_pending_orders(db: Session):
    return (
        db.query(Order).options(joinedload(Order.product))
        .filter(Order.status == OrderStatus.WAITING_DELIVERY)
        .order_by(desc(Order.created_at))
        .all()
    )
