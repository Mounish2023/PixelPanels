
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Table, func, Boolean
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
    prompt_data_info = Column(JSON)  # Store additional configurations set by the user for prompt
    topic = Column(String(50)) # can be categorized as "educational", "health", "ethics" etc.
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    story_text = Column(String(5000))  # Store the generated story
    data_info = Column(JSON)  # Keep metadata like image/audio URLs from Azure
    user_id = Column(Integer, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)
    # Add text search vector
    story_search_vector = Column(String)  # For full-text search capabilities
    view_count = Column(Integer, default=0)
    search_vector = Column(String)  # For full-text search
    
    creator = relationship("User", back_populates="comics")
    panels = relationship("Panel", back_populates="comic")
    likes = relationship("Like", back_populates="comic")
    views = relationship("View", back_populates="comic")

class Panel(Base):
    __tablename__ = "panels"
    
    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey("comics.id"))
    sequence = Column(Integer, nullable=False)
    text_content = Column(String(500))  # Store panel text in database
    description = Column(String(1000))  # Store image generation prompt
    image_url = Column(String(255))     # Store Azure blob URL for image
    audio_url = Column(String(255))     # Store Azure blob URL for audio
    
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
