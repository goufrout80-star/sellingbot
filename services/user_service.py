from sqlalchemy.orm import Session
from models import User, UserRole

def get_or_create_user(db: Session, user_id: int, username: str, first_name: str, last_name: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def set_user_role(db: Session, user_id: int, role: UserRole):
    user = get_user_by_id(db, user_id)
    if user:
        user.role = role
        db.commit()
        db.refresh(user)
    return user

def set_user_authenticated(db: Session, user_id: int, is_authenticated: bool):
    user = get_user_by_id(db, user_id)
    if user:
        user.is_authenticated = is_authenticated
        db.commit()
        db.refresh(user)
    return user
