from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models import (
    SubredditConfig, QuestionSet, ConfigUpdateRequest, ConfigResponse
)

router = APIRouter(prefix="/config", tags=["config"])

@router.get("", response_model=ConfigResponse)
async def get_config(
    subreddit_name: str = "devvit",
    db: Session = Depends(get_db)
):
    """Get subreddit verification configuration."""
    
    config = db.query(SubredditConfig).filter(
        SubredditConfig.subreddit_name == subreddit_name
    ).first()
    
    if not config:
        # Create default config if not exists
        config = SubredditConfig(
            subreddit_name=subreddit_name,
            verification_enabled=True,
            max_attempts=3,
            attempt_timeout_hours=10,
            spam_threshold=85,
            additional_rules={
                "require_email": False,
                "minimum_karma": 0,
                "account_age_days": 0
            }
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config

@router.post("", response_model=ConfigResponse)
async def update_config(
    request: ConfigUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update subreddit verification configuration."""
    
    config = db.query(SubredditConfig).filter(
        SubredditConfig.subreddit_name == request.subreddit_name
    ).first()
    
    if not config:
        config = SubredditConfig(subreddit_name=request.subreddit_name)
        db.add(config)
    
    # Update fields
    update_data = request.model_dump(exclude_unset=True, exclude={"subreddit_name"})
    for field, value in update_data.items():
        setattr(config, field, value)
    
    config.updated_at = "now()"
    
    try:
        db.commit()
        db.refresh(config)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Configuration update failed")
    
    return config

@router.get("/question-sets", response_model=List[dict])
async def list_question_sets(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List available question sets for verification."""
    
    query = db.query(QuestionSet)
    if active_only:
        query = query.filter(QuestionSet.is_active == True)
    
    question_sets = query.order_by(QuestionSet.id.desc()).all()
    
    return [
        {
            "id": qs.id,
            "name": qs.name,
            "question_count": len(qs.questions) if qs.questions else 0,
            "is_active": qs.is_active,
            "created_at": qs.created_at
        }
        for qs in question_sets
    ]

@router.post("/question-sets")
async def create_question_set(
    name: str,
    questions: list,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Create a new question set for verification."""
    
    question_set = QuestionSet(
        name=name,
        questions=questions,
        is_active=is_active
    )
    
    db.add(question_set)
    db.commit()
    db.refresh(question_set)
    
    return {
        "id": question_set.id,
        "name": question_set.name,
        "question_count": len(question_set.questions),
        "is_active": question_set.is_active
    }

@router.put("/question-sets/{question_set_id}")
async def update_question_set(
    question_set_id: int,
    name: str,
    questions: list,
    is_active: bool,
    db: Session = Depends(get_db)
):
    """Update an existing question set."""
    
    question_set = db.query(QuestionSet).filter(
        QuestionSet.id == question_set_id
    ).first()
    
    if not question_set:
        raise HTTPException(status_code=404, detail="Question set not found")
    
    question_set.name = name
    question_set.questions = questions
    question_set.is_active = is_active
    
    db.commit()
    db.refresh(question_set)
    
    return {
        "id": question_set.id,
        "name": question_set.name,
        "question_count": len(question_set.questions),
        "is_active": question_set.is_active
    }

@router.delete("/question-sets/{question_set_id}")
async def delete_question_set(
    question_set_id: int,
    db: Session = Depends(get_db)
):
    """Delete a question set (if not in use)."""
    
    question_set = db.query(QuestionSet).filter(
        QuestionSet.id == question_set_id
    ).first()
    
    if not question_set:
        raise HTTPException(status_code=404, detail="Question set not found")
    
    # Check if question set is being used
    usage_count = db.query(VerificationAttempt).filter(
        VerificationAttempt.question_set_id == question_set_id
    ).count()
    
    if usage_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete question set that is in use"
        )
    
    db.delete(question_set)
    db.commit()
    
    return {"message": "Question set deleted successfully"}

@router.get("/defaults")
async def get_default_config():
    """Get default configuration values."""
    
    return {
        "verification_enabled": True,
        "max_attempts": 3,
        "attempt_timeout_hours": 10,
        "spam_threshold": 85,
        "webhook_url": None,
        "additional_rules": {
            "require_email": False,
            "minimum_karma": 0,
            "account_age_days": 0,
            "max_pinned_posts": 2,
            "min_comment_karma": 0,
            "min_post_karma": 0
        },
        "default_questions": [
            {
                "id": "q1",
                "text": "What is the purpose of this subreddit?",
                "type": "multiple_choice",
                "options": [
                    "Community discussions",
                    "Promotional content",
                    "Technical support",
                    "All of the above"
                ],
                "correct_answer": "All of the above",
                "points": 1
            },
            {
                "id": "q2",
                "text": "How long has your Reddit account been active?",
                "type": "number",
                "correct_answer": "1",
                "points": 1,
                "instructions": "Enter in months"
            },
            {
                "id": "q3",
                "text": "Have you read the subreddit rules?",
                "type": "boolean",
                "correct_answer": "true",
                "points": 1
            }
        ]
    }