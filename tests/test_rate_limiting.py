"""
Tests for rate limiting functionality in the verification system.
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import VerificationAttempt, RateLimitTracker
from app.services.rate_limiter import RateLimiter


class TestRateLimiting:
    """
    Test cases for maximum 3 verification attempts per 24-hour period
    """
    
    def test_max_3_attempts_per_day(self, client, db_session):
        """Test users are limited to 3 verification attempts in 24 hours"""
        
        from app.models import User
        user_id = "test_user_rate_limit"
        
        user = User(id=user_id, username="rate_limit_test")
        db_session.add(user)
        db_session.commit()
        
        # First 3 attempts should succeed
        for i in range(3):
            response = client.post("/api/verify/start", json={
                "user_id": user_id,
                "reddit_post_url": f"https://reddit.com/r/tech/comments/{i}"
            })
            assert response.status_code == 200
            assert response.json()["rate_limit_status"] == "active"
        
        # 4th attempt should be blocked
        response = client.post("/api/verify/start", json={
            "user_id": user_id,
            "reddit_post_url": "https://reddit.com/r/tech/comments/3"
        })
        
        assert response.status_code == 429
        assert "3 attempts" in response.json()["detail"]
    
    def test_rate_limiter_reset_after_24_hours(self, client, db_session):
        """Test rate limit resets after 24 hours"""
        
        from app.models import User
        user_id = "test_user_reset"
        
        user = User(id=user_id, username="reset_test")
        db_session.add(user)
        db_session.commit()
        
        # Simulate 3 attempts made yesterday
        for i in range(3):
            tracker = RateLimitTracker(
                user_id=user_id,
                attempt_date=datetime.now() - timedelta(hours=25),
                is_rate_limited=True,
                attempt_count=i+1
            )
            db_session.add(tracker)
        
        db_session.commit()
        
        # New attempt should succeed after 24 hours
        response = client.post("/api/verify/start", json={
            "user_id": user_id,
            "reddit_post_url": "https://reddit.com/r/tech/comments/new"
        })
        
        assert response.status_code == 200
    
    def test_rate_limiter_partial_day_tracking(self, client, db_session):
        """Test rate limiter tracks attempts within partial day boundaries"""
        
        from app.models import User
        user_id = "test_user_partial"
        
        user = User(id=user_id, username="partial_test")
        db_session.add(user)
        db_session.commit()
        
        # Add attempts from mixed time periods
        current_time = datetime.now()
        
        # 2 attempts from current day
        for i in range(2):
            tracker = RateLimitTracker(
                user_id=user_id,
                attempt_date=current_time - timedelta(hours=i),
                is_rate_limited=False,
                attempt_count=i+1
            )
            db_session.add(tracker)
        
        # 1 attempt from previous day
        old_tracker = RateLimitTracker(
            user_id=user_id,
            attempt_date=current_time - timedelta(days=1, hours=1),
            is_rate_limited=True,
            attempt_count=1
        )
        db_session.add(old_tracker)
        db_session.commit()
        
        # Should allow 1 more attempt (2 used today)
        response = client.post("/api/verify/start", json={
            "user_id": user_id,
            "reddit_post_url": "https://reddit.com/r/tech/comments/new2"
        })
        assert response.status_code == 200
        
        # 2nd attempt should block (3 total for today)
        response = client.post("/api/verify/start", json={
            "user_id": user_id,
            "reddit_post_url": "https://reddit.com/r/tech/comments/new3"
        })
        assert response.status_code == 429
    
    def test_rate_limiter_ignores_expired_attempts(self, client, db_session):
        """Test expired verification attempts don't count toward rate limit"""
        
        from app.models import User, VerificationStatus
        user_id = "test_user_expire"
        
        user = User(id=user_id, username="expire_test")
        db_session.add(user)
        
        # Create 2 expired attempts
        for i in range(2):
            attempt = VerificationAttempt(
                user_id=user_id,
                reddit_post_url=f"url{i}",
                status=VerificationStatus.EXPIRED,
                created_at=datetime.now() - timedelta(days=i+1)
            )
            db_session.add(attempt)
        
        # Create 1 active attempt  
        active_attempt = VerificationAttempt(
            user_id=user_id,
            reddit_post_url="url_active",
            status=VerificationStatus.IN_PROGRESS,
            created_at=datetime.now() - timedelta(hours=1)
        )
        db_session.add(active_attempt)
        db_session.commit()
        
        # Should allow 2 more verifications (only active ones count)
        response = client.get(f"/api/verify/rate-limit/{user_id}")
        rate_limit_data = response.json()
        
        assert rate_limit_data["current_count"] == 1
        assert rate_limit_data["remaining"] == 2
        assert rate_limit_data["is_limited"] == False
    
    def test_rate_limiter_crossed_midnight_reset(self, client, db_session):
        """Test rate limiter properly handles midnight rollover"""
        
        from app.models import User
        user_id = "test_user_midnight"
        
        user = User(id=user_id, username="midnight_test")
        db_session.add(user)
        db_session.commit()
        
        # Simulate 3 attempts right before midnight
        with patch('app.services.rate_limiter.datetime.now') as mock_datetime:
            # Mock time just before midnight (23:50:00)
            mock_datetime.now.return_value = datetime(
                year=2024, month=1, day=15, hour=23, minute=50, second=0
            )
            
            for i in range(3):
                response = client.post("/api/verify/start", json={
                    "user_id": user_id,
                    "reddit_post_url": f"url_{i}"
                })
                assert response.status_code == 200
            
            # 4th attempt same day should fail
            response = client.post("/api/verify/start", json={
                "user_id": user_id,
                "reddit_post_url": "url_should_fail"
            })
            assert response.status_code == 429
            
            # Mock time after midnight (00:01:00 next day)
            mock_datetime.now.return_value = datetime(
                year=2024, month=1, day=16, hour=0, minute=1, second=0
            )
            
            # New attempt after midnight should succeed
            response = client.post("/api/verify/start", json={
                "user_id": user_id,
                "reddit_post_url": "url_new_day"
            })
            assert response.status_code == 200
    
    def test_rate_limiter_respects_user_limits_isolation(self, client, db_session):
        """Test rate limits are isolated per user"""
        
        from app.models import User
        user1_id = "user1_isolated"
        user2_id = "user2_isolated"
        
        user1 = User(id=user1_id, username="user1")
        user2 = User(id=user2_id, username="user2")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Exhaust user1's limit
        for i in range(3):
            response = client.post("/api/verify/start", json={
                "user_id": user1_id,
                "reddit_post_url": f"user1_url{i}"
            })
            assert response.status_code == 200
        
        # User1 should now be blocked
        response = client.post("/api/verify/start", json={
            "user_id": user1_id,
            "reddit_post_url": "user1_url_blocked"
        })
        assert response.status_code == 429
        
        # User2 should still have full access
        response = client.post("/api/verify/start", json={
            "user_id": user2_id,
            "reddit_post_url": "user2_url_allowed"
        })
        assert response.status_code == 200
    
    def test_rate_limiter_admin_override(self, client, db_session):
        """Test administrators can override rate limiting"""
        
        from app.models import User
        user_id = "test_admin_override"
        
        user = User(id=user_id, username="admin_test")
        db_session.add(user)
        db_session.commit()
        
        # Exhaust user's limit
        for i in range(3):
            response = client.post("/api/verify/start", json={
                "user_id": user_id,
                "reddit_post_url": f"admin_url{i}"
            })
            assert response.status_code == 200
        
        # User should be blocked
        response = client.post("/api/verify/start", json={
            "user_id": user_id,
            "reddit_post_url": "admin_blocked"
        })
        assert response.status_code == 429
        
        # Admin override should allow additional attempt
        with patch('app.auth.verify_admin') as mock_admin_auth:
            mock_admin_auth.return_value = {"user_id": "admin_user", "role": "admin"}
            
            response = client.post("/api/verify/start", headers={
                "Override-Rate-Limit": "true"
            }, json={
                "user_id": user_id,
                "reddit_post_url": "admin_allowed"
            })
            assert response.status_code == 200
    
    def test_rate_limiter_status_endpoint(self, client, db_session):
        """Test rate limiter status endpoint provides accurate info"""
        
        from app.models import User
        user_id = "test_status_user"
        
        user = User(id=user_id, username="status_test")
        db_session.add(user)
        db_session.commit()
        
        # Make one attempt
        response = client.post("/api/verify/start", json={
            "user_id": user_id,
            "reddit_post_url": "status_url1"
        })
        assert response.status_code == 200
        
        # Check rate limit status
        response = client.get(f"/api/verify/rate-limit/{user_id}")
        status = response.json()
        
        assert status["user_id"] == user_id
        assert status["current_count"] == 1
        assert status["limit"] == 3
        assert status["remaining"] == 2
        assert status["is_limited"] == False
        assert "reset_time" in status
        assert status["reset_hours"] <= 24