from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer


class BlogPostBase(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    cover_image_url: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: bool = False


class BlogPostCreate(BlogPostBase):
    pass


class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    cover_image_url: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None


class BlogPost(BlogPostBase):
    id: int
    author_id: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", "published_at")
    def serialize_datetime(self, value: Optional[datetime], _info) -> Optional[str]:
        return value.isoformat() if value else None
