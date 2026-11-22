import re
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blog import BlogPost
from app.schemas.blog import BlogPostCreate, BlogPostUpdate
from app.core.config import settings
from app.core.html_sanitize import sanitize_html


class BlogService:
    def _generate_slug(self, title: str) -> str:
        slug = title.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")

    async def get_by_id(self, db: AsyncSession, post_id: int) -> Optional[BlogPost]:
        result = await db.execute(select(BlogPost).filter(BlogPost.id == post_id))
        return result.scalars().first()

    async def get_by_slug(self, db: AsyncSession, slug: str, published_only: bool = True) -> Optional[BlogPost]:
        stmt = select(BlogPost).filter(BlogPost.slug == slug)
        if published_only:
            stmt = stmt.filter(BlogPost.is_published == True)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_posts(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        published_only: bool = True,
        search: Optional[str] = None,
    ) -> List[BlogPost]:
        stmt = select(BlogPost)
        if published_only:
            stmt = stmt.filter(BlogPost.is_published == True)
        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.filter((BlogPost.title.ilike(term)) | (BlogPost.slug.ilike(term)))
        stmt = stmt.order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _unique_slug(self, db: AsyncSession, slug: str, exclude_id: Optional[int] = None) -> str:
        base = slug
        counter = 1
        while True:
            existing = await self.get_by_slug(db, slug, published_only=False)
            if not existing or (exclude_id and existing.id == exclude_id):
                return slug
            slug = f"{base}-{counter}"
            counter += 1

    async def create(self, db: AsyncSession, data: BlogPostCreate, author_id: Optional[int] = None) -> BlogPost:
        slug = await self._unique_slug(db, data.slug or self._generate_slug(data.title))
        content = sanitize_html(data.content) if settings.SANITIZE_HTML else data.content
        post = BlogPost(
            title=data.title,
            slug=slug,
            content=content,
            excerpt=data.excerpt,
            cover_image_url=data.cover_image_url,
            meta_description=data.meta_description,
            is_published=data.is_published,
            author_id=author_id,
            published_at=datetime.now(timezone.utc) if data.is_published else None,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    async def update(self, db: AsyncSession, post_id: int, data: BlogPostUpdate) -> Optional[BlogPost]:
        post = await self.get_by_id(db, post_id)
        if not post:
            return None
        update = data.model_dump(exclude_unset=True)
        if settings.SANITIZE_HTML and "content" in update and update["content"] is not None:
            update["content"] = sanitize_html(update["content"])
        if "slug" in update and update["slug"]:
            update["slug"] = await self._unique_slug(db, update["slug"], exclude_id=post_id)
        elif "title" in update and "slug" not in update:
            update["slug"] = await self._unique_slug(db, self._generate_slug(update["title"]), exclude_id=post_id)

        was_published = post.is_published
        for field, value in update.items():
            setattr(post, field, value)

        if post.is_published and not was_published and not post.published_at:
            post.published_at = datetime.now(timezone.utc)
        if not post.is_published:
            pass  # keep published_at history

        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    async def delete(self, db: AsyncSession, post_id: int) -> bool:
        post = await self.get_by_id(db, post_id)
        if not post:
            return False
        await db.delete(post)
        await db.commit()
        return True


blog_service = BlogService()
