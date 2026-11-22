from typing import List, Optional, Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ALLOWED_UNITS = ("kg", "pound", "ton")


class OrderItemBase(BaseModel):
    product_variant_id: int
    quantity: Decimal = Field(..., gt=0)
    quantity_unit: Literal["kg", "pound", "ton"] = "kg"


class OrderItemCreate(OrderItemBase):
    pass


class ProductNameForOrder(BaseModel):
    name: str
    slug: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductVariantForOrder(BaseModel):
    id: int
    product_id: int
    sku: str
    price: Decimal
    product: Optional[ProductNameForOrder] = None

    model_config = ConfigDict(from_attributes=True)


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    price_at_purchase: Decimal
    variant: Optional[ProductVariantForOrder] = None

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    shipping_address: Optional[dict] = None
    shipping_address_id: Optional[int] = None
    billing_address_id: Optional[int] = None


class OrderCreate(OrderBase):
    payment_method: str = "inquiry"
    payment_method_id: Optional[str] = None
    promo_code: Optional[str] = None


class GuestOrderItemIn(BaseModel):
    product_variant_id: int
    quantity: Decimal = Field(..., gt=0)
    quantity_unit: Literal["kg", "pound", "ton"] = "kg"

    @field_validator("quantity_unit", mode="before")
    @classmethod
    def normalize_unit(cls, v: str) -> str:
        u = (v or "kg").strip().lower()
        if u in ("lb", "lbs", "pounds"):
            return "pound"
        if u in ("tons", "tonne", "tonnes"):
            return "ton"
        if u not in ALLOWED_UNITS:
            raise ValueError("quantity_unit must be kg, pound, or ton")
        return u


class GuestOrderCreate(BaseModel):
    """Public inquiry order — no auth / no payment gateway."""
    customer_name: str = Field(..., min_length=2, max_length=255, description="Contact person name")
    customer_email: EmailStr
    customer_country: str = Field(..., min_length=2, max_length=100, description="Delivery country")
    customer_address: str = Field(..., min_length=3, max_length=1000, description="Street address")
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_notes: Optional[str] = Field(None, max_length=2000)
    city: Optional[str] = Field(None, max_length=255)
    items: List[GuestOrderItemIn] = Field(..., min_length=1)

    @field_validator("customer_name", "customer_country", "customer_address", mode="before")
    @classmethod
    def strip_required_text(cls, v):
        if v is None:
            return v
        return str(v).strip()


class OrderUpdate(BaseModel):
    status: str


class OrderReplyCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class OrderReplyOut(BaseModel):
    id: int
    order_id: int
    admin_user_id: Optional[int] = None
    message: str
    sent_to_email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Order(OrderBase):
    id: int
    user_id: Optional[int] = None
    order_number: Optional[str] = None
    status: str
    total_amount: Decimal
    stripe_payment_id: Optional[str] = None
    payment_method: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_country: Optional[str] = None
    customer_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    promo_code_id: Optional[int] = None
    discount_amount: Optional[Decimal] = None
    created_at: datetime
    items: List[OrderItem] = []
    replies: List[OrderReplyOut] = []

    model_config = ConfigDict(from_attributes=True)


class OrderAdmin(Order):
    """Admin order payload (customer fields already on Order for guest inquiries)."""
    model_config = ConfigDict(from_attributes=True)
