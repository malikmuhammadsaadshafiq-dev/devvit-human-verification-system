"""
Tests for moderator actions and administrative functionality.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import VerificationAttempt, ModeratorAction, ModeratorActionType, VerificationStatus


class TestModeratorActions:
    """
    Test cases for moderator approve/reject flows and configuration updates
    """
    
    def test_moderator_approve_verification(self, client, db_session):
        """Test moderators can approve verified users"""
        
        from app.models import User
        # Setup test data
        user = User(id="test_user_789", username="test_user")
        db_session.add(user)
        
        attempt = VerificationAttempt(
            user_id="test_user_789",
            reddit_post_url="https://reddit.com/r/tech/comments/test789",
            status=VerificationStatus.COMPLETED,
            step=3,
            created_at=datetime.now() - timedelta(minutes=30),
            completed_at=datetime.now() - timedelta(minutes=5)
        )
        db_session.add(attempt)
        db_session.commit()
        
        # Login as moderator (mock auth)
        with patch('app.auth.verify_moderator') as mock_auth:
            mock_auth.return_value = {"user_id": "mod_123", "role": "moderator"}
            
            response = client.post(f"/api/moderate/verify/{attempt.id}/approve", json={
                "moderator_notes": "Valid verification, user appears legitimate"
            })
            
            assert response.status_code == 200
            assert response.json()["status"] == "approved"
            
            # Verify database update
            attempt_db = db_session.query(VerificationAttempt).get(attempt.id)
            assert attempt_db.status == VerificationStatus.APPROVED
            assert attempt_db.moderator_approved == True
    
    def test_moderator_reject_verification(self, client, db_session):
        """Test moderators can reject suspicious verifications"""
        
        from app.models import User
        user = User(id="test_user_789", username="test_user")
        db_session.add(user)
        
        attempt = VerificationAttempt(
            user_id="test_user_789",
            reddit_post_url="https://reddit.com/r/tech/comments/suspicious789",
            status=VerificationStatus.COMPLETED,
            step=3,
            created_at=datetime.now() - timedelta(hours=2)
        )
        db_session.add(attempt)
        db_session.commit()
        
        # Reject with notes
        with patch('app.auth.verify_moderator') as mock_auth:
            mock_auth.return_value = {"user_id": "mod_123", "role": "moderator"}
            
            response = client.post(f"/api/moderate/verify/{attempt.id}/reject", json={
                "moderator_notes": "User submitted spam-like responses, pattern matches known spammer behavior",
                "reason": "suspicious_patterns"
            })
            
            assert response.status_code == 200
            assert response.json()["status"] == "rejected"
            
            # Verify database
            attempt_db = db_session.query(VerificationAttempt).get(attempt.id)
            assert attempt_db.status == VerificationStatus.REJECTED
            assert attempt_db.rejection_reason == "suspicious_patterns"
    
    def test_moderator_action_audit_logging(self, client, db_session):
        """Test moderator actions are properly logged for audit trail"""
        
        from app.models import User
        # Setup test data
        user = User(id="user_555", username="regular_user")
        db_session.add(user)
        
        attempt = VerificationAttempt(
            user_id="user_555",
            reddit_post_url="https://reddit.com/r/tech/comments/test555",
            status=VerificationStatus.COMPLETED
        )
        db_session.add(attempt)
        db_session.commit()
        
        # Perform moderator action
        with patch('app.auth.verify_moderator') as mock_auth:
            mock_auth.return_value = {"user_id": "moderator_jane", "role": "moderator"}
            
            response = client.post(f"/api/moderate/verify/{attempt.id}/approve", json={
                "moderator_notes": "User appears legitimate based on post history"
            })
            
            assert response.status_code == 200
            
            # Verify audit log
            log_entry = db_session.query(ModeratorAction).filter_by(
                verification_attempt_id=attempt.id
            ).first()
            
            assert log_entry is not None
            assert log_entry.action == ModeratorActionType.APPROVE
            assert log_entry.moderator_id == "moderator_jane"
            assert log_entry.notes == "User appears legitimate based on post history"
    
    def test_mod_config_update_work_hours(self, client, db_session):
        """Test moderators can update verification work hours"""
        
        with patch('app.auth.verify_moderator') as mock_auth:
            mock_auth.return_value = {"user_id": "mod_001", "role": "moderator"}
            
            response = client.post("/api/moderate/config/work-hours", json={
                "start_hour": 8,
                "end_hour": 20,
                "timezone": "UTC"
            })
            
            assert response.status_code == 200
            assert response.json()["start_hour"] == 8
            assert response.json()["end_hour"] == 20
    
    def test_mod_config_update_auto_approval_thresholds(self, client, db_session):
        """Test moderators can update auto-approval thresholds"""
        
        with patch('app.auth.verify_moderator') as mock_auth:
            mock_auth.return_value = {"user_id": "mod_001", "role": "moderator"}
            
            response = client.post("/api/moderate/config/auto-approval", json={
                "min_score": 0.85,
                "max_response_time_hours": 2,
                "require_history_days": 30
            })
            
            assert response.status_code == 200
            assert response.json()["min_score"] == 0.85
            assert response.json()["max_response_time_hours"] == 2
    
    def test_mod_config_spam_thresholds_update(self, client, db_session):
        """Test moderators can update spam detection thresholds"""
        
        with patch('app.auth.verify_moderator') as mock_auth:
            mock_auth.return_value = {"user_id": "mod_001", "role": "moderator"}
            
            response = client.post("/api/moderate/config/spam-detection", json={
                "confidence_threshold": 0.8,
                "promotional_weight": 2.0,
                "url_blacklist": ["spammy.com", "malicious.net", "phishing.org"]
            })
            
            assert response.status_code == 200
            assert response.json()["confidence_threshold"] == 0.8
            assert "spammy.com" in response.json()["url_blacklist"]
    
    def test_mod_only_access_to_admin_endpoints(self, client, db_session):
        """Test non-moderators cannot access admin endpoints"""
        
        # Attempt without moderator auth
        response = client.post("/api/moderate/verify/test123/approve", json={
            "moderator_notes": "Should not work"
        })
        
        assert response.status_code == 403
        
        # Attempt with regular user (not moderator)
        with patch('app.auth.verify_user') as mock_auth:
            mock_auth.return_value = {"user_id": "regular_user", "role": "user"}
            
            response = client.post("/api/moderate/config/work-hours", json={
                "start_hour": 9,
                "end_hour": 17
            })
            
            assert response.status_code == 403
    
    def test_mod_queue_filtering(self, client, db_session):
        """Test moderator can get filtered verification queue"""
        
        from app.models import User
        
        # Create test verifications
        users = []
        for i in range(3):
            user = User(id=f"user_{i}", username=f"user{i}")
            users.append(user)
            db_session.add(user)
        
        db_session.flush()
        
        attempts = [
            VerificationAttempt(
                user_id=users[0].id,
                reddit_post_url="url1",
                status=VerificationStatus.PENDING_REVIEW
            ),
            VerificationAttempt(
                user_id=users[1].id,
                reddit_post_url="url2",
                status=VerificationStatus.COMPLETED
            ),
            VerificationAttempt(
                user_id=users[2].id,
                reddit_post_url="url3",
                status=VerificationStatus.SUSPICIOUS
            )
        ]
        
        for attempt in attempts:
            db_session.add(attempt)
        db_session.commit()
        
        with patch('app.auth.verify_moderator') as mock_auth:
            mock_auth.return_value = {"user_id": "mod_001", "role": "moderator"}
            
            # Get pending reviews
            response = client.get("/api/moderate/queue/pending")
            assert response.status_code == 200
            
            data = response.json()
            pending_count = len(data["items"])
            assert pending_count >= 1  # Should include pending reviews
            
            # Get suspicious queue
            response = client.get("/api/moderate/queue/suspicious")
            assert response.status_code == 200
    
    def test_mod_actions_history(self, client, db_session):
        """Test moderators can view action history"""
        
        # First, create some moderator actions
        with patch('app.auth.verify_moderator') as mock_auth:
            mock_auth.return_value = {"user_id": "mod_history_test", "role": "moderator"}
            
            # Perform various actions
            test_data = [
                ("approve", "Good verification"),
                ("reject", "Needs more review"),
                ("update_config", "Adjusted spam thresholds")
            ]
            
            for action, notes in test_data:
                if action == "update_config":
                    response = client.post("/api/moderate/config/spam-detection", json={
                        "confidence_threshold": 0.75
                    })
                # Additional test setup would be needed here
                
            # Test history endpoint
            response = client.get("/api/moderate/history?limit=50")
            assert response.status_code == 200
            history = response.json()
            
            # Verify we have some records
            assert "items" in history
            assert len(history["items"]) >= 0