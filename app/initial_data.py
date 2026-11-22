import asyncio
import logging
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.product import Category
from datetime import datetime, timedelta, timezone

from app.models.page import Page
from app.models.blog import BlogPost
# Import other models to ensure they are registered for relationships
from app.models.cart import Cart
from app.models.wishlist import Wishlist
from app.models.order import Order
from app.models.review import Review
from app.models.user_group import UserGroup
from app.models.permission import Permission
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ABOUT_US_CONTENT = """
<h2>Our Story</h2>
<p>Nepal Origin brings the purity of the Himalayas to your daily wellness. We source premium herbal teas, Ayurvedic roots, medicinal spices, and natural botanicals from trusted growers across Nepal.</p>
<p>Every product is chosen for authenticity, careful handling, and the belief that <strong>purity always wins</strong>.</p>
<h2>What We Stand For</h2>
<ul>
  <li><strong>100% Natural &amp; Organic</strong> — clean ingredients without unnecessary additives</li>
  <li><strong>Trusted Quality</strong> — selected with care from mountain farms and cooperatives</li>
  <li><strong>Transparent Sourcing</strong> — herbs with clear origin and honest stories</li>
  <li><strong>Customer Care</strong> — dedicated support for every inquiry, local or worldwide</li>
</ul>
<h2>From Nepal to You</h2>
<p>Whether you are discovering Himalayan basil tea, turmeric, ashwagandha, or traditional wellness blends, our mission is simple: deliver nature&rsquo;s goodness for a healthier life.</p>
<p>Have questions about bulk orders or product details? <a href="/contact">Contact us</a> — we are happy to help.</p>
""".strip()

FAQS_CONTENT = """
<h2>Ordering &amp; Inquiries</h2>
<p><strong>How do I place an order?</strong><br />
Browse our herbal products, open a product page, and submit an inquiry with your details. Our team will follow up to confirm availability, pricing, and delivery.</p>
<p><strong>Do you accept bulk or wholesale requests?</strong><br />
Yes. Mention quantity and destination in your inquiry, and we will share a tailored quote.</p>
<p><strong>Can I pay in NPR or USD?</strong><br />
Product prices are shown in both NPR and USD. Final payment details are confirmed when we respond to your inquiry.</p>

<h2>Products &amp; Quality</h2>
<p><strong>Are your products natural and organic?</strong><br />
We focus on natural Himalayan herbs, teas, Ayurvedic roots, and spices sourced with purity and care. Specific certifications are listed on each product when available.</p>
<p><strong>How should I store herbal products?</strong><br />
Keep them in a cool, dry place away from direct sunlight. Follow any storage notes on the product packaging or detail page.</p>
<p><strong>Do you offer samples?</strong><br />
Sample availability depends on the product. Ask in your inquiry and we will advise.</p>

<h2>Shipping &amp; Delivery</h2>
<p><strong>Where do you deliver?</strong><br />
We fulfill orders across Nepal and can arrange international shipping depending on the product and destination.</p>
<p><strong>How long does delivery take?</strong><br />
Local Nepal deliveries are typically faster; international timelines vary by courier and customs. We share estimates when confirming your inquiry.</p>
<p><strong>Is there free shipping?</strong><br />
Free shipping may apply on qualifying orders (for example, over NPR 2000). Exact terms are confirmed with your order.</p>

<h2>Support</h2>
<p><strong>How can I contact you?</strong><br />
Use our <a href="/contact">Contact</a> page, or email us with your question. We are here to help with products, orders, and wellness guidance.</p>
<p><strong>Can I track my inquiry or order?</strong><br />
Yes. Use <a href="/orders">Track Order</a> with your inquiry details, or reply to the confirmation email we send you.</p>
""".strip()


DUMMY_BLOGS = [
    {
        "title": "The Healing Power of Himalayan Herbs",
        "slug": "healing-power-himalayan-herbs",
        "excerpt": "Discover why herbs grown in Nepal’s high mountains are prized for purity and potency.",
        "meta_description": "Learn how Himalayan altitude, soil, and tradition shape Nepal Origin herbal quality.",
        "content": """
<h2>Why altitude matters</h2>
<p>Herbs grown in the Himalayas face cooler nights, strong sunlight, and mineral-rich soils. That stress often concentrates beneficial plant compounds — one reason Nepali botanicals are sought after worldwide.</p>
<p>At Nepal Origin, we work with growers who harvest carefully, dry properly, and protect the integrity of each batch from mountain to pouch.</p>
<h2>Everyday wellness rituals</h2>
<ul>
  <li>Start the morning with a cup of tulsi or ginger lemongrass tea</li>
  <li>Use turmeric and medicinal spices in warm meals</li>
  <li>Choose single-origin roots like ashwagandha when you want traditional Ayurvedic support</li>
</ul>
<p>Purity always wins — and that begins with how herbs are grown and handled.</p>
""".strip(),
    },
    {
        "title": "How to Brew the Perfect Herbal Tea",
        "slug": "how-to-brew-perfect-herbal-tea",
        "excerpt": "Simple steps to get more aroma, flavor, and benefits from your Nepal Origin tea blends.",
        "meta_description": "Brewing guide for Himalayan basil, ginger lemongrass, and other herbal teas.",
        "content": """
<h2>Water, temperature, and time</h2>
<p>Most herbal teas prefer near-boiling water. Use fresh water, pour over the leaves or blend, and steep covered for 5–8 minutes so the volatile oils stay in the cup.</p>
<ol>
  <li>Heat clean water to a rolling boil</li>
  <li>Add 1–2 teaspoons of herbal tea per cup</li>
  <li>Steep covered for 5–8 minutes</li>
  <li>Strain and enjoy plain, or with a touch of honey</li>
</ol>
<h2>Tips from the mountains</h2>
<p>Do not boil the herbs for long periods if you want a lighter, aromatic cup. For stronger digestive blends like ginger lemongrass, a slightly longer steep is fine.</p>
<p>Store tea in a cool, dry place away from sunlight to keep freshness.</p>
""".strip(),
    },
    {
        "title": "Turmeric &amp; Timur: Nepal’s Kitchen Pharmacy",
        "slug": "turmeric-timur-kitchen-pharmacy",
        "excerpt": "Two everyday Nepali spices with deep roots in food and traditional wellness.",
        "meta_description": "Explore turmeric fingers and timur berry — staples of Nepali kitchens and herbal traditions.",
        "content": """
<h2>Turmeric fingers</h2>
<p>High-curcumin turmeric has long been used in cooking and home remedies. Choose well-dried fingers with a deep color and earthy aroma.</p>
<h2>Timur berry</h2>
<p>Nepali timur (Sichuan pepper relative) brings citrusy heat and numbing warmth. A pinch transforms soups, pickles, and spice mixes.</p>
<p>Both spices remind us that wellness often starts in the kitchen — with ingredients that are natural, fragrant, and honestly sourced.</p>
""".strip(),
    },
    {
        "title": "Buying Herbs Online: What to Look For",
        "slug": "buying-herbs-online-what-to-look-for",
        "excerpt": "A practical checklist before you inquire about herbal products from Nepal.",
        "meta_description": "Tips for choosing quality herbal teas, roots, and spices when ordering online.",
        "content": """
<h2>Checklist for quality</h2>
<ul>
  <li><strong>Origin</strong> — clear sourcing from Nepal or named growing regions</li>
  <li><strong>Form</strong> — whole, cut, powder, or tea blend suited to your use</li>
  <li><strong>Freshness</strong> — aroma and color that match the plant</li>
  <li><strong>Transparency</strong> — honest descriptions without miracle claims</li>
</ul>
<h2>How Nepal Origin works</h2>
<p>Browse products, open a detail page, and send an inquiry. We confirm availability, pricing in NPR/USD, and delivery options for Nepal and international destinations.</p>
<p>Questions? Visit our <a href="/contact">Contact</a> page or read the <a href="/page/faqs">FAQs</a>.</p>
""".strip(),
    },
]


async def _ensure_page(
    db,
    *,
    title: str,
    slug: str,
    content: str,
    meta_description: str,
    footer_order: int = 0,
) -> None:
    result = await db.execute(select(Page).filter(Page.slug == slug))
    page = result.scalars().first()
    if page:
        logger.info("%s page already exists", title)
        return
    db.add(
        Page(
            title=title,
            slug=slug,
            content=content,
            meta_description=meta_description,
            is_published=True,
            show_in_footer=True,
            footer_order=footer_order,
            show_in_header=False,
            header_order=0,
            page_type="page",
        )
    )
    await db.commit()
    logger.info("%s page created (slug: %s)", title, slug)


async def _ensure_blogs(db) -> None:
    result = await db.execute(select(User).filter(User.is_superuser == True).limit(1))
    author = result.scalars().first()
    author_id = author.id if author else None
    now = datetime.now(timezone.utc)

    for i, post in enumerate(DUMMY_BLOGS):
        existing = await db.execute(select(BlogPost).filter(BlogPost.slug == post["slug"]))
        if existing.scalars().first():
            logger.info("Blog already exists: %s", post["slug"])
            continue
        db.add(
            BlogPost(
                title=post["title"],
                slug=post["slug"],
                excerpt=post["excerpt"],
                content=post["content"],
                meta_description=post["meta_description"],
                cover_image_url=None,
                is_published=True,
                author_id=author_id,
                published_at=now - timedelta(days=len(DUMMY_BLOGS) - i),
            )
        )
        logger.info("Blog created: %s", post["slug"])
    await db.commit()


async def create_initial_data() -> None:
    async with SessionLocal() as db:
        # 1. Create dummy Nepal Origin admin
        logger.info("Creating Nepal Origin admin...")
        for email, password, name in [
            ("admin@nepalorigin.store", "Admin@123", "Nepal Origin Admin"),
            ("proxydhakal@gmail.com", "admin@123", "Proxy Dhakal"),
        ]:
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    full_name=name,
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                    role="admin",
                )
                db.add(user)
                logger.info("Admin created: %s", email)
            else:
                user.hashed_password = get_password_hash(password)
                user.is_superuser = True
                user.role = "admin"
                user.is_active = True
                db.add(user)
                logger.info("Admin updated: %s", email)
        await db.commit()

        # 2. Create herbal categories
        logger.info("Creating initial categories...")
        categories = [
            "Himalayan Herbs",
            "Ayurvedic Roots",
            "Medicinal Spices",
            "Wellness Teas",
        ]
        
        for cat_name in categories:
            result = await db.execute(select(Category).filter(Category.name == cat_name))
            cat = result.scalars().first()
            if not cat:
                cat = Category(name=cat_name, slug=cat_name.lower().replace(" ", "-"))
                db.add(cat)
        
        await db.commit()
        logger.info("Categories created")

        # 3. CMS pages (editable in Admin → Pages with CKEditor)
        logger.info("Ensuring CMS pages...")
        await _ensure_page(
            db,
            title="About Us",
            slug="about-us",
            content=ABOUT_US_CONTENT,
            meta_description="Learn about Nepal Origin — premium Himalayan herbal products crafted with purity and care.",
            footer_order=1,
        )
        await _ensure_page(
            db,
            title="FAQs",
            slug="faqs",
            content=FAQS_CONTENT,
            meta_description="Frequently asked questions about Nepal Origin herbal products, inquiries, shipping, and support.",
            footer_order=2,
        )

        # 4. Dummy blog posts (editable in Admin → Blogs)
        logger.info("Ensuring dummy blog posts...")
        await _ensure_blogs(db)

        logger.info("For full herbal products + sample orders run: python -m scripts.seed_dummy_data")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_initial_data())
