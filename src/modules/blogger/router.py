from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .models import BlogPost
from src.core.auth import current_active_user, User

router = APIRouter(tags=["blogger"])

# --- Public Routes ---
@router.get("/posts", response_model=List[BlogPost])
async def list_published_posts():
    return await BlogPost.find(BlogPost.status == "published").to_list()

@router.get("/posts/{slug}", response_model=BlogPost)
async def get_post(slug: str):
    post = await BlogPost.get_by_slug(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# --- Private Routes ---
@router.post("/posts", response_model=BlogPost, dependencies=[Depends(current_active_user)])
async def create_post(post: BlogPost):
    await post.insert()
    return post

@router.put("/posts/{id}", response_model=BlogPost, dependencies=[Depends(current_active_user)])
async def update_post(id: str, update_data: dict):
    post = await BlogPost.get(id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await post.set(update_data)
    return post
