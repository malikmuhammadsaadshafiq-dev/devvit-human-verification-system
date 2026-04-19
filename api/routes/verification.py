from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import uuid
import random
from typing import List

from ..database import get_db
from ..models import (
    User, VerificationAttempt, QuestionSet, SubredditConfig,
    StartVerificationRequest, StartVerificationResponse,
    CompleteVerificationRequest, CompleteVerificationResponse,
    VerificationStatus, CompleteVerificationResponse
)
from ..services import webhook_service

router = APIRouter(prefix="/verify", tags=["verification"])

@router.post("/start", response_model=StartVerificationResponse)
async def start_verification(
    request: StartVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new verification process for a user."""
    
    # Get subreddit config (assuming single subreddit for now)
    config = db.query(SubredditConfig).first()
    if not config or not config.verification_enabled:
        raise HTTPException(status_code=400, detail="Verification is not enabled")
    
    # Get or create user
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        user = User(username=request.username)
        db.add(user)
        db.commit()
    
    # Check if user has active verification attempts
    active_attempt = db.query(VerificationAttempt).filter(
        and_(
            VerificationAttempt.user_id == user.id,
            VerificationAttempt.status == VerificationStatus.IN_PROGRESS,
            VerificationAttempt.expires_at > datetime.utcnow()
        )
    ).first()
    
    if active_attempt:
        raise HTTPException(
            status_code=400,
            detail="Verification already in progress"
        )
    
    # Check max attempts
    recent_attempts = db.query(VerificationAttempt).filter(
        and_(
            VerificationAttempt.user_id == user.id,
            VerificationAttempt.started_at > datetime.utcnow() - timedelta(hours=config.attempt_timeout_hours)
        )
    ).count()
    
    if recent_attempts >= config.max_attempts:
        raise HTTPException(
            status_code=429,
            detail="Maximum verification attempts exceeded"
        )
    
    # Get active question set
    question_set = db.query(QuestionSet).filter(QuestionSet.is_active == True).first()
    if not question_set:
        raise HTTPException(status_code=500, detail="No active question set available")
    
    # Create verification attempt
    expires_at = datetime.utcnow() + timedelta(hours=config.attempt_timeout_hours)
    attempt = VerificationAttempt(
        user_id=user.id,
        question_set_id=question_set.id,
        status=VerificationStatus.IN_PROGRESS,
        expires_at=expires_at
    )
    
    db.add(attempt)
    db.commit()
    
    # Update user stats
    user.verification_attempts += 1
    user.last_attempt_at = datetime.utcnow()
    db.commit()
    
    # Send webhook notification
    if config.webhook_url:
        background_tasks.add_task(
            webhook_service.send_webhook,
            config.webhook_url,
            {
                "action": "verification_started",
                "username": user.username,
                "attempt_id": attempt.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return StartVerificationResponse(
        attempt_id=attempt.id,
        questions=question_set.questions,
        expires_at=expires_at
    )

@router.post("/complete", response_model=CompleteVerificationResponse)
async def complete_verification(
    request: CompleteVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Complete verification by submitting answers."""
    
    attempt = db.query(VerificationAttempt).filter(
        and_(
            VerificationAttempt.id == request.attempt_id,
            VerificationAttempt.status == VerificationStatus.IN_PROGRESS
        )
    ).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Verification attempt not found")
    
    if attempt.expires_at < datetime.utcnow():
        attempt.status = VerificationStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=400, detail="Verification attempt has expired")
    
    # Calculate score
    question_set = attempt.question_set
    max_score = 0
    user_score = 0
    
    if question_set.questions:
        for question in question_set.questions:
            max_score += question.get("points", 1)
            
            # Find user's answer
            user_answer = next(
                (a.answer for a in request.answers if a.question_id == str(question["id"])),
                None
            )
            
            if user_answer and user_answer.lower() == question.get("correct_answer", "").lower():
                user_score += question.get("points", 1)
    
    score_percentage = (user_score / max_score * 100) if max_score > 0 else 0
    
    # Get subreddit config for spam threshold
    config = db.query(SubredditConfig).first()
    spam_threshold = config.spam_threshold if config else 85
    
    # Determine result
    passed = score_percentage >= spam_threshold
    
    if passed:
        attempt.status = VerificationStatus.APPROVED
        attempt.user.verification_status = VerificationStatus.APPROVED
    else:
        attempt.status = VerificationStatus.REJECTED
        attempt.user.verification_status = VerificationStatus.REJECTED
    
    attempt.score = int(score_percentage)
    attempt.answers = [a.dict() for a in request.answers]
    attempt.completed_at = datetime.utcnow()
    attempt.user.verified_at = datetime.utcnow() if passed else None
    
    db.commit()
    
    # Send webhook notification
    if config and config.webhook_url:
        background_tasks.add_task(
            webhook_service.send_webhook,
            config.webhook_url,
            {
                "action": "verification_completed",
                "username": attempt.user.username,
                "attempt_id": attempt.id,
                "score": score_percentage,
                "status": attempt.status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return CompleteVerificationResponse(
        status=attempt.status,
        score=int(score_percentage),
        passed=passed
    )

@router.get("/users/{username}/status")
async def get_user_status(
    username: str,
    db: Session = Depends(get_db)
):
    """Get the current verification status of a user."""
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {
            "username": username,
            "verification_status": VerificationStatus.PENDING,
            "verification_attempts": 0,
            "last_attempt_at": None,
            "verified_at": None,
            "can_attempt": True
        }
    
    # Check if user can make another attempt
    config = db.query(SubredditConfig).first()
    can_attempt = True
    if config:
        recent_attempts = db.query(VerificationAttempt).filter(
            and_(
                VerificationAttempt.user_id == user.id,
                VerificationAttempt.started_at > datetime.utcnow() - timedelta(hours=config.attempt_timeout_hours)
            )
        ).count()
        
        can_attempt = recent_attempts < config.max_attempts
    
    return {
        "username": user.username,
        "verification_status": user.verification_status,
        "verification_attempts": user.verification_attempts,
        "last_attempt_at": user.last_attempt_at,
        "verified_at": user.verified_at,
        "can_attempt": can_attempt
    }