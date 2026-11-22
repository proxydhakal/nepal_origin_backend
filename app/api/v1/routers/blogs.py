from typing import Any, List, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_active_user, get_current_user_optional
from app.core.database import get_db
from app.core.query_params import str_to_bool
from app.core.storage import save_content_image
from app.models.user import User
from app.schemas.blog import BlogPost, BlogPostCreate, BlogPostUpdate
from app.services.blog_service import blog_service

router = APIRouter()


@router.get("/", response_model=List[BlogPost])
async def list_blogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    published_only: Union[str, bool, int] = Query(True),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Any:
    published = str_to_bool(published_only)
    if current_user and current_user.is_superuser:
        published = False if published_only in (False, "false", "0", 0) else published
        # Admin listing: when explicitly asking for all, published_only=false
        if str(published_only).lower() in ("false", "0"):
            published = False
    posts = await blog_service.list_posts(
        db, skip=skip, limit=limit, published_only=published, search=search
    )
    return posts


@router.get("/{slug}", response_model=BlogPost)
async def get_blog(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Any:
    published_only = not (current_user and current_user.is_superuser)
    post = await blog_service.get_by_slug(db, slug, published_only=published_only)
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return post


@router.post("/upload-image")
async def upload_blog_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    relative_path = await save_content_image(file)
    return {"url": "/" + relative_path.replace("\\", "/")}


@router.post("/", response_model=BlogPost, status_code=201)
async def create_blog(
    data: BlogPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await blog_service.create(db, data, author_id=current_user.id)


@router.patch("/{post_id}", response_model=BlogPost)
async def update_blog(
    post_id: int,
    data: BlogPostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    post = await blog_service.update(db, post_id, data)
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return post


@router.delete("/{post_id}")
async def delete_blog(
    post_id: int,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    ok = await blog_service.delete(db, post_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Blog post not found")
    response.status_code = 204
