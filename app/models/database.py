from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Boolean, func, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship



class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    comics: Mapped[List["Comic"]] = relationship("Comic", back_populates="creator")


class Comic(Base):
    __tablename__ = "comics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt_data_info: Mapped[Optional[dict]] = mapped_column(JSON)
    topic: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    story_text: Mapped[Optional[str]] = mapped_column(String(5000))
    audio_url: Mapped[Optional[str]] = mapped_column(String(255))
    data_info: Mapped[Optional[dict]] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)

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
    __table_args__ = (
        UniqueConstraint('comic_id', 'user_id', name='uix_comic_user'),
        Index('idx_comic_user', 'comic_id', 'user_id')
    )
    


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

class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comic_id: Mapped[int] = mapped_column(ForeignKey("comics.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    comic: Mapped[Comic] = relationship("Comic", back_populates="favorites")

class Trash(Base):
    __tablename__ = "trash"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comic_id: Mapped[int] = mapped_column(ForeignKey("comics.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    comic: Mapped[Comic] = relationship("Comic", back_populates="trash")

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

