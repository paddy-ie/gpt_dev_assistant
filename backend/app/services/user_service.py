from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.user import User
from app.security.password import get_password_hash, verify_password


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_user(self, email: str, password: str, full_name: str | None = None, is_superuser: bool = False) -> User:
        user = User(email=email.lower(), hashed_password=get_password_hash(password), full_name=full_name, is_superuser=is_superuser)
        self.session.add(user)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError("Email already registered") from exc
        self.session.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        statement = select(User).where(User.email == email.lower())
        user = self.session.exec(statement).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email.lower())
        return self.session.exec(statement).first()
