
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Table, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    comics = relationship("Comic", back_populates="creator")

class Comic(Base):
    __tablename__ = "comics"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    prompt = Column(String(500), nullable=False)
    style = Column(String(50))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    metadata = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    creator = relationship("User", back_populates="comics")
    panels = relationship("Panel", back_populates="comic")
    likes = relationship("Like", back_populates="comic")
    views = relationship("View", back_populates="comic")

class Panel(Base):
    __tablename__ = "panels"
    
    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey("comics.id"))
    sequence = Column(Integer, nullable=False)
    image_url = Column(String(255))
    text_content = Column(String(500))
    audio_url = Column(String(255))
    
    comic = relationship("Comic", back_populates="panels")

class Like(Base):
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey("comics.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    comic = relationship("Comic", back_populates="likes")
    user = relationship("User")

class View(Base):
    __tablename__ = "views"
    
    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey("comics.id"))
    viewed_at = Column(DateTime, server_default=func.now())
    
    comic = relationship("Comic", back_populates="views")
