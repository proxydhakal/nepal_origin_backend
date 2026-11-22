# Import all models to ensure SQLAlchemy can discover them
from app.models.user import User
from app.models.product import Category, Product, ProductVariant, ProductImage
from app.models.cart import Cart, CartItem
from app.models.wishlist import Wishlist, WishlistItem
from app.models.order import Order, OrderItem, OrderReply
from app.models.review import Review
from app.models.user_group import UserGroup
from app.models.permission import Permission
from app.models.site_config import SiteConfig
from app.models.promo import PromoCode, PromoCodeUsage
from app.models.blacklisted_token import BlacklistedToken
from app.models.address import Address
from app.models.page import Page
from app.models.blog import BlogPost
from app.models.contact_submission import ContactSubmission
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.models.verification_otp import VerificationOtp

__all__ = [
    'User',
    'Category',
    'Product',
    'ProductVariant',
    'ProductImage',
    'Cart',
    'CartItem',
    'Wishlist',
    'WishlistItem',
    'Order',
    'OrderItem',
    'OrderReply',
    'Review',
    'UserGroup',
    'Permission',
    'SiteConfig',
    'PromoCode',
    'PromoCodeUsage',
    'BlacklistedToken',
    'Address',
    'Page',
    'BlogPost',
    'ContactSubmission',
    'NewsletterSubscriber',
    'VerificationOtp',
]
