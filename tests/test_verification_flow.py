"""
Tests for the complete verification flow of the subreddit human verification system.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import VerificationAttempt, User, VerificationStep, VerificationStatus


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_reddit_client():
    with patch('app.services.reddit.RedditClient') as mock:
        instance = mock.return_value
        yield instance


class TestFullVerificationFlow:
    """
    Test cases for the complete verification flow
    """
    
    def test_full_verification_flow_success(self, client, db_session, mock_reddit_client):
        """Test a user successfully completing all 3 verification steps within 10 hours"""
        # Setup test user
        user = User(
            id="test_user_123",
            username="test_user",
            reddit_username="test_reddit_user"
        )
        db_session.add(user)
        db_session.commit()
        
        # Mock Reddit responses
        mock_reddit_client.get_submission.return_value = {
            "title": "Legitimate Question",
            "body": "This is a genuine post about technology",
            "author": "test_reddit_user",
            "created_utc": datetime.now().timestamp() - 3600  # 1 hour ago
        }
        
        # Step 1: Initial verification request
        response = client.post("/api/verify/start", json={
            "user_id": "test_user_123",
            "reddit_post_url": "https://reddit.com/r/technology/comments/test123"
        })
        assert response.status_code == 200
        attempt_id = response.json()["attempt_id"]
        
        # Step 2: First question/answer
        response = client.post(f"/api/verify/{attempt_id}/step1", json={
            "answer": "This is a genuine answer from the user"
        })
        assert response.status_code == 200
        assert response.json()["step"] == 1
        
        # Step 3: Second question/answer
        response = client.post(f"/api/verify/{attempt_id}/step2", json={
            "answer": "Additional validation response"
        })
        assert response.status_code == 200
        assert response.json()["step"] == 2
        
        # Step 4: Final verification complete
        response = client.post(f"/api/verify/{attempt_id}/complete")
        assert response.status_code == 200
        assert response.json()["status"] == "verified"
        
        # Verify attempt in database
        attempt = db_session.query(VerificationAttempt).filter_by(id=attempt_id).first()
        assert attempt.status == VerificationStatus.COMPLETED
        assert attempt.completed_at is not None
        assert (attempt.completed_at - attempt.created_at) < timedelta(hours=10)
    
    def test_verification_flow_timeout_after_10_hours(self, client, db_session, mock_reddit_client):
        """Test that verification attempts expire after 10 hours"""
        # Setup test data
        user = User(id="test_user_123", username="test_user")
        db_session.add(user)
        
        # Create old attempt (more than 10 hours ago)
        old_attempt = VerificationAttempt(
            user_id="test_user_123",
            reddit_post_url="https://reddit.com/r/tech/comments/test123",
            status=VerificationStatus.IN_PROGRESS,
            created_at=datetime.now() - timedelta(hours=12),
            step=1
        )
        db_session.add(old_attempt)
        db_session.commit()
        
        # Try to continue verification
        response = client.post(f"/api/verify/{old_attempt.id}/step2", json={
            "answer": "This should fail"
        })
        assert response.status_code == 400
        assert "expired" in response.json()["detail"]
        
    def test_verification_flow_resets_expired_attempts(self, client, db_session, mock_reddit_client):
        """Test that expired attempts are automatically reset"""
        user = User(id="test_user_123", username="test_user")
        db_session.add(user)
        
        old_attempt = VerificationAttempt(
            user_id="test_user_123",
            reddit_post_url="https://reddit.com/r/tech/comments/test123",
            status=VerificationStatus.IN_PROGRESS,
            created_at=datetime.now() - timedelta(hours=11),
            step=2
        )
        db_session.add(old_attempt)
        db_session.commit()
        
        # Create new attempt - should reset old one
        response = client.post("/api/verify/start", json={
            "user_id": "test_user_123",
            "reddit_post_url": "https://reddit.com/r/technology/comments/test456"
        })
        assert response.status_code == 200
        new_attempt_id = response.json()["attempt_id"]
        
        # Verify old attempt was marked expired
        old_attempt_db = db_session.query(VerificationAttempt).get(old_attempt.id)
        assert old_attempt_db.status == VerificationStatus.EXPIRED