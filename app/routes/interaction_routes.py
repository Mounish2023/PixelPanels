
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.database import Comic, Like, View
from datetime import datetime

router = APIRouter()

@router.post("/comics/{comic_id}/like")
async def like_comic(comic_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    comic_result = await db.execute(select(Comic).filter(Comic.id == comic_id))
    comic = comic_result.scalar_one_or_none()
    
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    
    existing_like_result = await db.execute(select(Like).filter(
        Like.comic_id == comic_id,
        Like.user_id == user_id
    ))
    existing_like = existing_like_result.scalar_one_or_none()
    
    if existing_like:
        comic.like_count -=1
        await db.delete(existing_like)
        await db.commit()
        return {"message": "Like removed"}
    
    new_like = Like(comic_id=comic_id, user_id=user_id)
    db.add(new_like)
    comic.like_count += 1
    await db.commit()
    return {"message": "Comic liked"}

@router.post("/comics/{comic_id}/view")
async def record_view(comic_id: int, db: AsyncSession = Depends(get_db)):
    comic_result = await db.execute(select(Comic).filter(Comic.id == comic_id))
    comic = comic_result.scalar_one_or_none()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    
    new_view = View(comic_id=comic_id, viewed_at=datetime.utcnow())
    
    db.add(new_view)
    comic.view_count += 1
    await db.commit()
    return {"message": "View recorded"}

# @router.get("/comics/{comic_id}/stats")
# async def get_comic_stats(comic_id: int, db: AsyncSession = Depends(get_db)):
#     comic = db.execute(Comic).filter(Comic.id == comic_id).first()
#     if not comic:
#         raise HTTPException(status_code=404, detail="Comic not found")
    
#     likes_count = db.query(Like).filter(Like.comic_id == comic_id).count()
#     views_count = db.query(View).filter(View.comic_id == comic_id).count()
    
#     return {
#         "likes": likes_count,
#         "views": views_count
#     }
