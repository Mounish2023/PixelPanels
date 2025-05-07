
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database import Comic, Like, View
from datetime import datetime

router = APIRouter()

@router.post("/comics/{comic_id}/like")
async def like_comic(comic_id: int, user_id: int, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    
    existing_like = db.query(Like).filter(
        Like.comic_id == comic_id,
        Like.user_id == user_id
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"message": "Like removed"}
    
    new_like = Like(comic_id=comic_id, user_id=user_id)
    db.add(new_like)
    db.commit()
    return {"message": "Comic liked"}

@router.post("/comics/{comic_id}/view")
async def record_view(comic_id: int, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    
    new_view = View(comic_id=comic_id, viewed_at=datetime.utcnow())
    db.add(new_view)
    db.commit()
    return {"message": "View recorded"}

@router.get("/comics/{comic_id}/stats")
async def get_comic_stats(comic_id: int, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    
    likes_count = db.query(Like).filter(Like.comic_id == comic_id).count()
    views_count = db.query(View).filter(View.comic_id == comic_id).count()
    
    return {
        "likes": likes_count,
        "views": views_count
    }
