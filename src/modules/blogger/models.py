from typing import Optional
from src.core.models import AuditMixin
from beanie import Document, Indexed

class BlogPost(Document, AuditMixin):
    title: str
    slug: Indexed(str, unique=True)
    content: str
    summary: Optional[str] = None
    status: str = "draft" # draft, published

    class Settings:
        name = "blog_posts"

    @classmethod
    async def get_by_slug(cls, slug: str) -> Optional["BlogPost"]:
        return await cls.find_one(cls.slug == slug)
