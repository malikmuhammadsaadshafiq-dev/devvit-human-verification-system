from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional

from ..database import get_db
from ..models import (
    User, VerificationAttempt, VerificationStatus,
    ModeratorApprovalRequest, UserResponse
)
from ..services import webhook_service

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/approve")
async def approve_verification(
    request: ModeratorApprovalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Moderator approval/rejection of a verification attempt."""
    
    attempt = db.query(VerificationAttempt).filter(
        and_(
            VerificationAttempt.id == request.attempt_id,
            VerificationAttempt.user.has(username=request.username)
        )
    ).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Verification attempt not found")
    
    # Update attempt status
    attempt.status = VerificationStatus.APPROVED if request.approved else VerificationStatus.REJECTED
    attempt.moderator_notes = request.notes
    attempt.completed_at = datetime.utcnow()
    
    # Update user status
    user = attempt.user
    user.verification_status = VerificationStatus.APPROVED if request.approved else VerificationStatus.REJECTED
    user.verified_at = datetime.utcnow() if request.approved else None
    user.verification_notes = request.notes
    
    db.commit()
    
    # Send webhook notification
    config = db.query(User.__table__.metadata.tables["subreddit_config"]).first()
    if config and config.webhook_url:
        background_tasks.add_task(
            webhook_service.send_webhook,
            config.webhook_url,
            {
                "action": "verification_approved" if request.approved else "verification_rejected",
                "username": user.username,
                "attempt_id": attempt.id,
                "moderator_notes": request.notes,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return {
        "username": user.username,
        "status": attempt.status,
        "notes": request.notes
    }

@router.get("/pending", response_model=List[dict])
async def get_pending_verifications(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get list of pending verifications for moderation."""
    
    pending = db.query(VerificationAttempt).filter(
        VerificationAttempt.status == VerificationStatus.IN_PROGRESS
    ).order_by(
        VerificationAttempt.started_at.asc()
    ).limit(limit).offset(offset).all()
    
    return [
        {
            "attempt_id": attempt.id,
            "username": attempt.user.username,
            "started_at": attempt.started_at,
            "expires_at": attempt.expires_at,
            "questions": attempt.question_set.questions if attempt.question_set else [],
            "answers": attempt.answers if attempt.answers else []
        }
        for attempt in pending
    ]

@router.get("/users", response_model=List[dict])
async def list_users(
    verified_only: bool = False,
    username_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List users with filtering options."""
    
    query = db.query(User)
    
    if verified_only:
        query = query.filter(User.verification_status == VerificationStatus.APPROVED)
    
    if username_filter:
        query = query.filter(User.username.contains(username_filter))
    
    users = query.order_by(User.created_at.desc()).limit(limit).offset(offset).all()
    
    return [
        {
            "username": user.username,
            "verification_status": user.verification_status,
            "verified_at": user.verified_at,
            "verification_attempts": user.verification_attempts,
            "last_attempt_at": user.last_attempt_at,
            "created_at": user.created_at
        }
        for user in users
    ]

@router.delete("/users/{username}")
async def reset_user_verification(
    username: str,
    db: Session = Depends(get_db)
):
    """Reset a user's verification status (admin action)."""
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Reset user status
    user.verification_status = VerificationStatus.PENDING
    user.verification_attempts = 0
    user.last_attempt_at = None
    user.verified_at = None
    user.verification_notes = None
    
    # Clean up old attempts
    expired_attempts = db.query(VerificationAttempt).filter(
        and_(
            VerificationAttempt.user_id == user.id,
            or_(
                VerificationAttempt.status == VerificationStatus.EXPIRED,
                VerificationAttempt.status == VerificationStatus.REJECTED
            )
        )
    ).delete()
    
    db.commit()
    
    return {"message": f"User {username} verification reset successfully"}

@router.get("/stats")
async def get_verification_stats(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get verification statistics."""
    
    from datetime import datetime, timedelta
    
    since = datetime.utcnow() - timedelta(days=days)
    
    total_attempts = db.query(VerificationAttempt).count()
    recent_attempts = db.query(VerificationAttempt).filter(
        VerificationAttempt.started_at > since
    ).count()
    
    approved = db.query(VerificationAttempt).filter(
        VerificationAttempt.status == VerificationStatus.APPROVED
    ).count()
    
    rejected = db.query(VerificationAttempt).filter(
        VerificationAttempt.status == VerificationStatus.REJECTED
    ).count()
    
    expired = db.query(VerificationAttempt).filter(
        VerificationAttempt.status == VerificationStatus.EXPIRED
    ).count()
    
    pending = db.query(VerificationAttempt).filter(
        and_(
            VerificationAttempt.status == VerificationStatus.IN_PROGRESS,
            VerificationAttempt.expires_at > datetime.utcnow()
        )
    ).count()
    
    total_users = db.query(User).count()
    verified_users = db.query(User).filter(
        User.verification_status == VerificationStatus.APPROVED
    ).count()
    
    return {
        "period": "last_30_days" if days == 30 else f"last_{days}_days",
        "verification_attempts": {
            "total": total_attempts,
            "recent": recent_attempts,
            "approved": approved,
            "rejected": rejected,
            "expired": expired,
            "pending": pending
        },
        "users": {
            "total": total_users,
            "verified": verified_users,
            "verification_rate": (verified_users / total_users * 100) if total_users > 0 else 0
        }
    }