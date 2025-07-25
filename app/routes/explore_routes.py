from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_
from typing import List, Optional
from app.database import get_db
from app.models.database import Comic, Like, Favorite
from app.models.comic_models import searchComicResponse

router = APIRouter()

@router.get("/search", response_model=List[searchComicResponse])
async def search_comics(
    q:str = Query( description="Search query for title or text"),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Comic, User.username.label("creator_name"))
        .join(User, Comic.user_id == User.id)
        .filter(Comic.id == comic_id)
    )
    query = select(Comic).where(Comic.is_deleted == False)            

    pattern = f"%{q}%"
    query = query.where(or_(
        Comic.title.ilike(pattern),
        Comic.story_text.ilike(pattern)
    ))
    result = await db.execute(query)
    return result.scalars().all()

    

async def _fetch_comics(query, db: AsyncSession):
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/explore", response_model=List[Comic])
async def explore_comics(db: AsyncSession = Depends(get_db)):
    query = select(Comic)
    query = query.where(Comic.is_deleted == False)
    query = query.order_by(func.random()).limit(10)
    return await _fetch_comics(query, db)

@router.get("/comics", response_model=List[Comic])
async def list_comics(db: AsyncSession = Depends(get_db)):
    query = select(Comic)
    query = query.where(Comic.is_deleted == False)
    query = query.order_by(func.random()).limit(20)
    return await _fetch_comics(query, db)

@router.get("/top", response_model=List[Comic])
async def top_comics(db: AsyncSession = Depends(get_db)):
    query = select(Comic)
    query = query.where(Comic.is_deleted == False)
    query = query.order_by(desc(Comic.view_count)).limit(10)
    return await _fetch_comics(query, db)

@router.get("/likes/{user_id}", response_model=List[Comic])
async def liked_comics(user_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Comic)
    query = query.join(Like, Comic.id == Like.comic_id)
    query = query.where(Like.user_id == user_id, Comic.is_deleted == False)
    return await _fetch_comics(query, db)

@router.get("/my-media/{user_id}", response_model=List[Comic])
async def user_media(user_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Comic)
    query = query.where(Comic.user_id == user_id, Comic.is_deleted == False)
    return await _fetch_comics(query, db)

@router.get("/favorites/{user_id}", response_model=List[Comic])
async def favorites(user_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Comic)
    query = query.join(Favorite, Comic.id == Favorite.comic_id)
    query = query.where(Favorite.user_id == user_id, Comic.is_deleted == False)
    return await _fetch_comics(query, db)

@router.get("/trash/{user_id}", response_model=List[Comic])
async def trash(user_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Comic)
    query = query.where(Comic.user_id == user_id, Comic.is_deleted == True)
    return await _fetch_comics(query, db)
