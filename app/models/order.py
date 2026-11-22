from typing import List, Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.promo import PromoCode
    from app.models.address import Address
    from app.models.user import User


class Order(Base):
    __tablename__ = "order"

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), index=True, nullable=True)
    order_number: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    status: Mapped[str] = mapped_column(String, default="pending", index=True)  # pending, confirmed, processing, completed, cancelled
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    shipping_address: Mapped[dict] = mapped_column(JSON)  # address snapshot
    shipping_address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("address.id"), nullable=True)
    billing_address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("address.id"), nullable=True)
    stripe_payment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(20), default="inquiry", index=True)  # inquiry (no online payment)

    # Guest / inquiry customer details
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    promo_code_id: Mapped[Optional[int]] = mapped_column(ForeignKey("promocode.id"), nullable=True)
    discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    replies: Mapped[List["OrderReply"]] = relationship("OrderReply", back_populates="order", cascade="all, delete-orphan", order_by="OrderReply.created_at")
    promo_code_rel: Mapped[Optional["PromoCode"]] = relationship("PromoCode", back_populates="orders")
    shipping_address_rel: Mapped[Optional["Address"]] = relationship("Address", foreign_keys=[shipping_address_id])


class OrderItem(Base):
    __tablename__ = "orderitem"

    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), index=True)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("productvariant.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    quantity_unit: Mapped[str] = mapped_column(String(20), default="kg")  # kg, pound, ton
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant")


class OrderReply(Base):
    """Admin reply/message about an order (emailed to customer)."""
    __tablename__ = "orderreply"

    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), index=True)
    admin_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    sent_to_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="replies")
    admin_user: Mapped[Optional["User"]] = relationship("User")
