from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import math

from database import get_db
from models import NewsModel
from schemas import News, PaginatedNewsResponse, NewsResponse
from auth import get_current_user

router = APIRouter(prefix="", tags=["News"])

@router.post("/post")
async def post_news(
    data: News,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user["role"] != "admin":
        raise HTTPException(
        status_code=403, 
        detail="You are not allowed to use this feature"
        )

    post = NewsModel(
        date=data.date,
        title=data.title,
        content=data.content
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"message": "News posted successfully 🎉"}

@router.get("/read", response_model=PaginatedNewsResponse)
async def read_news(
    page: int = 1,
    limit: int = 10,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 10

    offset = (page - 1) * limit
    total_items = db.query(NewsModel).count()

    if total_items == 0:
        return PaginatedNewsResponse(
            total_items=0,
            total_pages=1,
            current_page=page,
            limit=limit,
            data=[]
        )

    posts = db.query(NewsModel).offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit)

    return PaginatedNewsResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        limit=limit,
        data=posts
    )

@router.get("/posts/{post_title}", response_model=list[NewsResponse])
async def search_news(
    post_title: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    found = db.query(NewsModel).filter(
        NewsModel.title.ilike(f"%{post_title}%")
    ).all()

    if not found:
        raise HTTPException(
        status_code=404, 
        detail="News not found"
        )
    return found