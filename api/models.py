from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum

Base = declarative_base()

class VerificationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    verification_status = Column(String(20), default=VerificationStatus.PENDING)
    verification_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    verifications = relationship("VerificationAttempt", back_populates="user")

class VerificationAttempt(Base):
    __tablename__ = "verification_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default=VerificationStatus.PENDING)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"))
    answers = Column(JSON, nullable=True)
    score = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    moderator_notes = Column(Text, nullable=True)
    webhook_sent = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="verifications")
    question_set = relationship("QuestionSet", back_populates="attempts")

class QuestionSet(Base):
    __tablename__ = "question_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    questions = Column(JSON, nullable=False)  # List of questions with options
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    attempts = relationship("VerificationAttempt", back_populates="question_set")

class SubredditConfig(Base):
    __tablename__ = "subreddit_config"
    
    id = Column(Integer, primary_key=True, index=True)
    subreddit_name = Column(String(100), unique=True, nullable=False)
    verification_enabled = Column(Boolean, default=True)
    max_attempts = Column(Integer, default=3)
    attempt_timeout_hours = Column(Integer, default=10)
    spam_threshold = Column(Integer, default=85)
    webhook_url = Column(String(500), nullable=True)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"))
    additional_rules = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic models
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    verification_status: VerificationStatus
    verification_attempts: int
    last_attempt_at: Optional[datetime]
    verified_at: Optional[datetime]
    created_at: datetime

class StartVerificationRequest(BaseModel):
    username: str

class StartVerificationResponse(BaseModel):
    attempt_id: int
    questions: List[Dict[str, Any]]
    expires_at: datetime

class VerificationAnswer(BaseModel):
    question_id: str
    answer: str

class CompleteVerificationRequest(BaseModel):
    attempt_id: int
    answers: List[VerificationAnswer]

class CompleteVerificationResponse(BaseModel):
    status: VerificationStatus
    score: int
    passed: bool

class ModeratorApprovalRequest(BaseModel):
    attempt_id: int
    username: str
    approved: bool
    notes: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    subreddit_name: str
    verification_enabled: Optional[bool] = None
    max_attempts: Optional[int] = None
    attempt_timeout_hours: Optional[int] = None
    spam_threshold: Optional[int] = None
    webhook_url: Optional[str] = None
    question_set_id: Optional[int] = None
    additional_rules: Optional[Dict[str, Any]] = None

class ConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    subreddit_name: str
    verification_enabled: bool
    max_attempts: int
    attempt_timeout_hours: int
    spam_threshold: int
    webhook_url: Optional[str]
    question_set_id: Optional[int]
    additional_rules: Dict[str, Any]

class WebhookPayload(BaseModel):
    action: str
    data: Dict[str, Any]