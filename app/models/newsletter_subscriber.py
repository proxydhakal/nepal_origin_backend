from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscriber"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    unsubscribe_token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
