from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_
from typing import List, Optional
from app.database import get_db
from app.models.database import Comic, Like

router = APIRouter()

@router.get("/search", response_model=List[Comic])
async def search_comics(
    q: Optional[str] = Query(None, description="Search query for title or text"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Comic).where(Comic.is_deleted == False)
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(
            Comic.title.ilike(pattern),
            Comic.story_text.ilike(pattern)
        ))
    if user_id is not None:
        query = query.where(Comic.user_id == user_id)
    if job_id is not None:
        query = query.where(Comic.id == job_id)

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

@router.get("/trash/{user_id}", response_model=List[Comic])
async def trash(user_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Comic)
    query = query.where(Comic.user_id == user_id, Comic.is_deleted == True)
    return await _fetch_comics(query, db)
