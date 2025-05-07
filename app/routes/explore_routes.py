
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from app.database import get_db
from app.models.database import Comic, User, Like, View

router = APIRouter()

@router.get("/search")
async def search_comics(
    q: str,
    user_id: Optional[str] = None,
    job_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Comic).filter(Comic.is_deleted == False)
    
    if q:
        query = query.filter(
            Comic.search_vector.ilike(f"%{q}%") |
            Comic.metadata['content'].astext.ilike(f"%{q}%")
        )
    
    if user_id:
        query = query.filter(Comic.user_id == user_id)
    
    if job_id:
        query = query.filter(Comic.id == job_id)
        
    return query.all()

@router.get("/explore")
async def explore_comics(db: Session = Depends(get_db)):
    return db.query(Comic)\
        .filter(Comic.is_deleted == False)\
        .order_by(func.random())\
        .limit(10)\
        .all()

@router.get("/comics")
async def list_comics(db: Session = Depends(get_db)):
    return db.query(Comic)\
        .filter(Comic.is_deleted == False)\
        .order_by(func.random())\
        .limit(20)\
        .all()

@router.get("/top")
async def top_comics(db: Session = Depends(get_db)):
    return db.query(Comic)\
        .filter(Comic.is_deleted == False)\
        .order_by(desc(Comic.view_count))\
        .limit(10)\
        .all()

@router.get("/likes/{user_id}")
async def liked_comics(user_id: int, db: Session = Depends(get_db)):
    return db.query(Comic)\
        .join(Like)\
        .filter(Like.user_id == user_id)\
        .filter(Comic.is_deleted == False)\
        .all()

@router.get("/my-media/{user_id}")
async def user_media(user_id: int, db: Session = Depends(get_db)):
    return db.query(Comic)\
        .filter(Comic.user_id == user_id)\
        .filter(Comic.is_deleted == False)\
        .all()

@router.get("/trash/{user_id}")
async def trash(user_id: int, db: Session = Depends(get_db)):
    return db.query(Comic)\
        .filter(Comic.user_id == user_id)\
        .filter(Comic.is_deleted == True)\
        .all()
