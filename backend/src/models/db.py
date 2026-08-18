from datetime import datetime
import enum
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class PostStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"

# 1. Events Table
class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="event", cascade="all, delete-orphan")
    prompts: Mapped[List["Prompt"]] = relationship("Prompt", back_populates="event", cascade="all, delete-orphan")

# 2. Prompts Table (Tied to Events)
class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="prompts")

# 3. Posts Table
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # DigitalOcean Spaces Storage References
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    spaces_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.PENDING)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event: Mapped[Optional["Event"]] = relationship("Event", back_populates="posts")
    publish_logs: Mapped[List["PublishLog"]] = relationship("PublishLog", back_populates="post")

# 4. WhatsApp & Platform Execution Logs
class PublishLog(Base):
    __tablename__ = "publish_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[Optional[int]] = mapped_column(ForeignKey("posts.id", ondelete="SET NULL"), nullable=True)
    platform: Mapped[str] = mapped_column(String(50), default="WHATSAPP")
    
    # Platform response details (Meta Message IDs, error payloads)
    whatsapp_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    response_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    post: Mapped[Optional["Post"]] = relationship("Post", back_populates="publish_logs")