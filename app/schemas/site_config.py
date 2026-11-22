from typing import Optional
from pydantic import BaseModel, Field


class SocialLinks(BaseModel):
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    youtube: Optional[str] = None
    tiktok: Optional[str] = None
    pinterest: Optional[str] = None
    # Optional custom icon URLs (paths or absolute)
    facebook_icon: Optional[str] = None
    twitter_icon: Optional[str] = None
    instagram_icon: Optional[str] = None
    linkedin_icon: Optional[str] = None
    youtube_icon: Optional[str] = None
    tiktok_icon: Optional[str] = None
    pinterest_icon: Optional[str] = None


class SiteConfigResponse(BaseModel):
    site_title: str
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    map_embed_url: Optional[str] = None
    map_latitude: Optional[str] = None
    map_longitude: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    social_links: Optional[dict] = None

    model_config = {"from_attributes": True}


class SiteConfigUpdate(BaseModel):
    site_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=100)
    contact_address: Optional[str] = None
    map_embed_url: Optional[str] = None
    map_latitude: Optional[str] = Field(None, max_length=50)
    map_longitude: Optional[str] = Field(None, max_length=50)
    logo_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)
    social_links: Optional[dict] = None
