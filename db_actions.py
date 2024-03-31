from typing import Optional

from crud_models import UserCreate , UserUpdate
from db import DBContext
from db_models import User
from security import hash_password, manager
from sqlalchemy.orm import Session
from typing import List


@manager.user_loader()
def get_user(email: str, db: Session = None) -> Optional[User]:
    """Return the user with the corresponding email"""
    if db is None:
        # No db session was provided so we have to manually create a new one
        # Closing of the connection is handled inside of DBContext.__exit__
        with DBContext() as db:
            return db.query(User).filter(User.email == email).first()
    else:
        return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new entry in the database user table"""
    user_data = user.dict()
    user_data["password"] = hash_password(user.password)
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user by their id."""
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete is not None:
        db.delete(user_to_delete)
        db.commit()
        return True
    return False


def update_user(db: Session, user_update: UserUpdate) -> Optional[User]:
    """Update user details."""
    user_to_update = db.query(User).filter(User.id == user_update.id).first()
    if user_to_update is not None:
        if user_update.email is not None:
            user_to_update.email = user_update.email
        if user_update.password is not None:
            user_to_update.password = hash_password(user_update.password)
        if user_update.is_admin is not None:
            user_to_update.is_admin = user_update.is_admin
        db.commit()
        db.refresh(user_to_update)
        return user_to_update
    return None



def get_users(db: Session, query: Optional[str] = None) -> List[User]:
    """Get a list of users optionally filtered by a query."""
    if query:
        return db.query(User).filter(User.email.contains(query)).all()
    return db.query(User).all()