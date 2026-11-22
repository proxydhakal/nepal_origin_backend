"""
Seed Nepal Origin herbal dummy data + admin user.
Usage (from backend root, venv active):
  python -m scripts.seed_dummy_data
"""
import asyncio
import logging
import random
import string
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.product import Category, Product, ProductVariant
from app.models.order import Order, OrderItem
from app.models.site_config import SiteConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_EMAIL = "admin@nepalorigin.store"
ADMIN_PASSWORD = "Admin@123"

HERB_CATEGORIES = [
    ("Himalayan Herbs", "himalayan-herbs", "Wild-crafted herbs from the Himalayas"),
    ("Ayurvedic Roots", "ayurvedic-roots", "Traditional Ayurvedic roots and rhizomes"),
    ("Medicinal Spices", "medicinal-spices", "Therapeutic spices and botanicals"),
    ("Wellness Teas", "wellness-teas", "Herbal tea blends for daily wellness"),
]

PRODUCTS = [
    ("Yarsagumba Powder", "yarsagumba-powder", "Premium Cordyceps sinensis powder.", 0, 12500, 95, 11000, 85, 50),
    ("Jatamansi Root", "jatamansi-root", "Dried Nardostachys jatamansi roots.", 0, 3200, 24, 2800, 21, 120),
    ("Chiraito Herb", "chiraito-herb", "Swertia chirayita whole herb.", 0, 1800, 14, None, None, 200),
    ("Ashwagandha Root", "ashwagandha-root", "Withania somnifera dried roots.", 1, 950, 7.5, 799, 6.2, 300),
    ("Turmeric Finger", "turmeric-finger", "High-curcumin turmeric fingers.", 2, 450, 3.5, 399, 3.0, 500),
    ("Timur Berry", "timur-berry", "Nepali Sichuan pepper (Zanthoxylum).", 2, 1200, 9, None, None, 150),
    ("Himalayan Basil Tea", "himalayan-basil-tea", "Tulsi herbal tea blend.", 3, 650, 5, 549, 4.2, 250),
    ("Ginger Lemongrass Tea", "ginger-lemongrass-tea", "Warming digestive tea blend.", 3, 580, 4.5, None, None, 280),
    ("Shilajit Resin", "shilajit-resin", "Purified Himalayan shilajit resin.", 0, 4500, 35, 3999, 30, 80),
    ("Neem Leaf Powder", "neem-leaf-powder", "Organic Azadirachta indica leaf powder.", 1, 720, 5.5, 649, 5.0, 180),
]


def _order_number() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


async def seed() -> None:
    async with SessionLocal() as db:
        # Admin user
        result = await db.execute(select(User).filter(User.email == ADMIN_EMAIL))
        admin = result.scalars().first()
        if not admin:
            admin = User(
                email=ADMIN_EMAIL,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                full_name="Nepal Origin Admin",
                is_active=True,
                is_superuser=True,
                is_verified=True,
                role="admin",
            )
            db.add(admin)
            logger.info("Created admin %s / %s", ADMIN_EMAIL, ADMIN_PASSWORD)
        else:
            admin.hashed_password = get_password_hash(ADMIN_PASSWORD)
            admin.is_superuser = True
            admin.is_active = True
            admin.role = "admin"
            db.add(admin)
            logger.info("Updated admin %s / %s", ADMIN_EMAIL, ADMIN_PASSWORD)

        # Also ensure legacy superuser exists
        result = await db.execute(select(User).filter(User.email == "proxydhakal@gmail.com"))
        legacy = result.scalars().first()
        if not legacy:
            db.add(
                User(
                    email="proxydhakal@gmail.com",
                    hashed_password=get_password_hash("admin@123"),
                    full_name="Proxy Dhakal",
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                    role="admin",
                )
            )

        # Site config
        cfg_res = await db.execute(select(SiteConfig).limit(1))
        cfg = cfg_res.scalars().first()
        if not cfg:
            cfg = SiteConfig(
                site_title="Nepal Origin",
                meta_description="Pure Himalayan herbal products — Purity Always Wins.",
                contact_email=ADMIN_EMAIL,
                contact_phone="+977-1-4000000",
                contact_address="Thamel, Kathmandu, Nepal",
                map_embed_url="https://maps.google.com/maps?q=Thamel%2C%20Kathmandu%2C%20Nepal&z=15&output=embed",
                map_latitude="27.7154",
                map_longitude="85.3123",
                logo_url="/static/brand/logo.png",
                favicon_url="/static/brand/favicon.png",
                social_links={
                    "facebook": "https://facebook.com/nepalorigin",
                    "instagram": "https://instagram.com/nepalorigin",
                },
            )
            db.add(cfg)
        else:
            if not cfg.contact_address:
                cfg.contact_address = "Thamel, Kathmandu, Nepal"
            if not cfg.map_embed_url:
                cfg.map_embed_url = "https://maps.google.com/maps?q=Thamel%2C%20Kathmandu%2C%20Nepal&z=15&output=embed"
            if not cfg.map_latitude:
                cfg.map_latitude = "27.7154"
                cfg.map_longitude = "85.3123"
            db.add(cfg)

        await db.flush()

        # Categories
        cat_ids: list[int] = []
        for name, slug, desc in HERB_CATEGORIES:
            res = await db.execute(select(Category).filter(Category.slug == slug))
            cat = res.scalars().first()
            if not cat:
                cat = Category(name=name, slug=slug, description=desc)
                db.add(cat)
                await db.flush()
            cat_ids.append(cat.id)

        # Products
        variant_ids: list[tuple[int, Decimal]] = []
        for i, (name, slug, desc, cat_idx, price, price_usd, offer, offer_usd, stock) in enumerate(PRODUCTS):
            res = await db.execute(select(Product).filter(Product.slug == slug))
            product = res.scalars().first()
            if product:
                vres = await db.execute(
                    select(ProductVariant).filter(ProductVariant.product_id == product.id).limit(1)
                )
                v = vres.scalars().first()
                if v:
                    v.price = Decimal(str(price))
                    v.price_usd = Decimal(str(price_usd))
                    v.offer_price = Decimal(str(offer)) if offer else None
                    v.offer_price_usd = Decimal(str(offer_usd)) if offer_usd else None
                    v.currency = "BOTH"
                    db.add(v)
                    variant_ids.append((v.id, Decimal(str(offer or price))))
                continue
            product = Product(
                name=name,
                slug=slug,
                description=desc,
                is_active=True,
                category_id=cat_ids[cat_idx],
                is_trending=i < 4,
                discount_percentage=Decimal("10") if offer else None,
            )
            db.add(product)
            await db.flush()
            variant = ProductVariant(
                product_id=product.id,
                sku=f"NO-{slug[:12].upper()}-{i+1:02d}",
                price=Decimal(str(price)),
                price_usd=Decimal(str(price_usd)),
                offer_price=Decimal(str(offer)) if offer else None,
                offer_price_usd=Decimal(str(offer_usd)) if offer_usd else None,
                currency="BOTH",
                stock_quantity=stock,
                attributes={"unit": "kg"},
            )
            db.add(variant)
            await db.flush()
            variant_ids.append((variant.id, Decimal(str(offer or price))))

        # Dummy inquiry orders for charts (last 14 days)
        order_count_res = await db.execute(select(Order).limit(1))
        has_orders = order_count_res.scalars().first() is not None
        if not has_orders and variant_ids:
            now = datetime.now(timezone.utc)
            for day_offset in range(14):
                for _ in range(random.randint(0, 3)):
                    vid, unit_price = random.choice(variant_ids)
                    qty = Decimal(str(random.choice([1, 2, 5, 10])))
                    total = unit_price * qty
                    created = now - timedelta(days=day_offset, hours=random.randint(0, 20))
                    order = Order(
                        user_id=None,
                        order_number=_order_number(),
                        status=random.choice(["pending", "confirmed", "processing", "completed"]),
                        total_amount=total,
                        shipping_address={
                            "street": "Thamel Marg",
                            "city": "Kathmandu",
                            "country": "Nepal",
                        },
                        payment_method="inquiry",
                        customer_name=random.choice(["Ram Sharma", "Sita Thapa", "John Miller", "Aisha Khan"]),
                        customer_email=f"buyer{random.randint(100,999)}@example.com",
                        customer_phone="+9779800000000",
                        customer_country="Nepal",
                        customer_notes="Dummy seed order",
                    )
                    db.add(order)
                    await db.flush()
                    order.created_at = created
                    db.add(
                        OrderItem(
                            order_id=order.id,
                            product_variant_id=vid,
                            quantity=qty,
                            quantity_unit="kg",
                            price_at_purchase=unit_price,
                        )
                    )
            logger.info("Seeded dummy inquiry orders")

        await db.commit()
        logger.info("Dummy data seed complete.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
