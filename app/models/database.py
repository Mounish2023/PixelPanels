from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Boolean, func, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship



class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    comics: Mapped[List["Comic"]] = relationship("Comic", back_populates="creator")


class Comic(Base):
    __tablename__ = "comics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt_data_info: Mapped[Optional[dict]] = mapped_column(JSON)
    topic: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    story_text: Mapped[Optional[str]] = mapped_column(String(5000))
    data_info: Mapped[Optional[dict]] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    story_search_vector: Mapped[Optional[str]] = mapped_column(String)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    search_vector: Mapped[Optional[str]] = mapped_column(String)

    creator: Mapped[User] = relationship("User", back_populates="comics")
    panels: Mapped[List["Panel"]] = relationship("Panel", back_populates="comic", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="comic", cascade="all, delete-orphan")
    views: Mapped[List["View"]] = relationship("View", back_populates="comic", cascade="all, delete-orphan")


class Panel(Base):
    __tablename__ = "panels"
    __table_args__ = (
        Index('idx_comic_sequence', 'comic_id', 'sequence'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comic_id: Mapped[int] = mapped_column(ForeignKey("comics.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    image_url: Mapped[Optional[str]] = mapped_column(String(255))

    comic: Mapped[Comic] = relationship("Comic", back_populates="panels")


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comic_id: Mapped[int] = mapped_column(ForeignKey("comics.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    comic: Mapped[Comic] = relationship("Comic", back_populates="likes")
    user: Mapped[User] = relationship("User")


class View(Base):
    __tablename__ = "views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comic_id: Mapped[int] = mapped_column(ForeignKey("comics.id"), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    comic: Mapped[Comic] = relationship("Comic", back_populates="views")
