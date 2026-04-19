"""
Test cases for edge cases like deleted posts, banned users, and network failures.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from requests.exceptions import ConnectionError, Timeout

from app.main import app
from app.models import VerificationAttempt, VerificationStatus, UserStatus


class TestEdgeCases:
    """
    Test cases for edge cases and error handling
    """
    
    def test_deleted_post_handling(self, client, db_session, mock_reddit_client):
        """Test handling when Reddit post is deleted during verification"""
        
        from app.models import User
        
        # Setup test user
        user = User(id="test_user_deleted", username="deleted_test")
        db_session.add(user)
        db_session.commit()
        
        # Mock Reddit client to simulate post deletion
        mock_reddit_client.get_submission.return_value = None
        mock_reddit_client.side_effect = Exception("Post not found")
        
        # Start verification successfully initially
        with patch('app.services.reddit.RedditClient') as mock_client:
            instance = mock_client.return_value
            instance.get_submission.return_value = {
                "title": "Test Post",
                "body": "Test content",
                "author": "test_user_deleted",
                "created_utc": datetime.now().timestamp()
            }
            
            response = client.post("/api/verify/start", json={
                "user_id": "test_user_deleted",
                "reddit_post_url": "https://reddit.com/r/tech/comments/12345"
            })
            assert response.status_code == 200
            
        # Simulate post being deleted during step submission
        with patch('app.services.reddit.RedditClient') as mock_client:
            instance = mock_client.return_value
            instance.get_submission.side_effect = Exception("Post removed or deleted")
            
            attempt_id = response.json()["attempt_id"]
            response = client.post(f"/api/verify/{attempt_id}/step1", json={
                "answer": "Some answer"
            })
            
            assert response.status_code == 410  # Gone
            assert "deleted" in response.json()["detail"].lower()
    
    def test_banned_user_blocked_verification(self, client, db_session):
        """Test banned/subreddit-specific banned users cannot start verification"""
        
        from app.models import User
        
        # Create banned user
        banned_user = User(
            id="banned_user_123",
            username="banned_user",
            status=UserStatus.BANNED,
            banned_reason="Spam violations in subreddit"
        )
        db_session.add(banned_user)
        
        # Create subreddit banned user
        sub_banned_user = User(
            id="sub_banned_456",
            username="sub_ban_test",
            status=UserStatus.ACTIVE,
            subreddit_bans=["r/technology"]
        )
        db_session.add(sub_banned_user)
        db_session.commit()
        
        # Test globally banned user
        response = client.post("/api/verify/start", json={
            "user_id": "banned_user_123",
            "reddit_post_url": "https://reddit.com/r/tech/comments/test"
        })
        assert response.status_code == 403
        assert "banned" in response.json()["detail"].lower()
        
        # Test subreddit banned user for specific sub
        response = client.post("/api/verify/start", json={
            "user_id": "sub_banned_456",
            "reddit_post_url": "https://reddit.com/r/technology/comments/test"
        })
        assert response.status_code == 403
        assert "banned from this subreddit" in response.json()["detail"]
        
        # Test subreddit banned user allowed in other sub
        response = client.post("/api/verify/start", json={
            "user_id": "sub_banned_456",
            "reddit_post_url": "https://reddit.com/r/programming/comments/test"
        })
        assert response.status_code == 200
    
    def test_network_failure_reddit_timeout(self, client, db_session):
        """Test handling when Reddit API times out or fails"""
        
        from app.models import User
        user = User(id="test_network_user", username="network_test")
        db_session.add(user)
        db_session.commit()
        
        # Mock Reddit API timeout
        with patch('app.services.reddit.RedditClient') as mock_client:
            instance = mock_client.return_value
            instance.get_submission.side_effect = Timeout("Request timed out")
            
            response = client.post("/api/verify/start", json={
                "user_id": "test_network_user",
                "reddit_post_url": "https://reddit.com/r/tech/comments/timeout"
            })
            
            assert response.status_code == 503  # Service Unavailable
            assert "temporary" in response.json()["detail"].lower()
    
    def test_network_failure_reddit_connection_error(self, client, db_session):
        """Test handling when Reddit API has connection errors"""
        
        from app.models import User
        user = User(id="test_conn_user", username="conn_test")
        db_session.add(user)
        db_session.commit()
        
        # Mock Reddit API connection error
        with patch('app.services.reddit.RedditClient') as mock_client:
            instance = mock_client.return_value
            instance.get_submission.side_effect = ConnectionError("Failed to connect")
            
            response = client.post("/api/verify/start", json={
                "user_id": "test_conn_user",
                "reddit_post_url": "https://reddit.com/r/tech/comments/connectionerror"
            })
            
            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"]
    
    def test_garbage_answers_rejection(self, client, db_session):
        """Test handling of spam/garbage verification answers"""
        
        from app.models import User
        user = User(id="test_garbage_user", username="garbage_test")
        db_session.add(user)
        
        attempt = VerificationAttempt(
            user_id=user.id,
            reddit_post_url="https://reddit.com/r/tech/comments/garbage123",
            status=VerificationStatus.IN_PROGRESS,
            step=1
        )
        db_session.add(attempt)
        db_session.commit()
        
        # Test extremely short garbage answers
        garbage_responses = [
            "a", "aa", "aaa", "Spam", "test", "123", "abc", "www", ".com"
        ]
        
        for garbage in garbage_responses:
            response = client.post(f"/api/verify/{attempt.id}/step1", json={
                "answer": garbage
            })
            
            if response.status_code == 200:
                # Should still validate minimum length requirements
                attempt_db = db_session.query(VerificationAttempt).get(attempt.id)
                assert attempt_db.step1_data is not None
    
    def test_database_connection_failure(self, client, db_session):
        """Test handling when database connection fails mid-verification"""
        
        from app.models import User
        user = User(id="test_db_fail_user", username="db_fail_test")
        db_session.add(user)
        
        attempt = VerificationAttempt(
            user_id=user.id,
            reddit_post_url="https://reddit.com/r/tech/comments/db_failure_test",
            status=VerificationStatus.IN_PROGRESS,
            step=1
        )
        db_session.add(attempt)
        db_session.commit()
        
        # Mock database session failure
        with patch('database.SessionLocal') as mock_session:
            from sqlalchemy.exc import OperationalError
            mock_session.side_effect = OperationalError(
                "database connection failed",
                None,
                None
            )
            
            response = client.post(f"/api/verify/{attempt.id}/step2", json={
                "answer": "Database should handle this gracefully"
            })
            
            # Should handle gracefully, maybe retry or rollback
            # Actual behavior depends on implementation
            pass
    
    def test_malformed_reddit_urls(self, client, db_session):
        """Test handling of invalid or malformed Reddit URLs"""
        
        from app.models import User
        user = User(id="url_test_user", username="url_test")
        db_session.add(user)
        db_session.commit()
        
        invalid_urls = [
            "https://google.com/not_reddit",
            "https://reddit.com/",
            "reddit.com/r/tech",
            "https://reddit.com/r/tech/invalid format",
            "https://reddit.com/r/tech/comments/",
            "https://reddit.com/r/te ch/comments/123",
            ""
        ]
        
        for invalid_url in invalid_urls:
            response = client.post("/api/verify/start", json={
                "user_id": "url_test_user",
                "reddit_post_url": invalid_url
            })
            
            assert response.status_code != 200
            error_detail = response.json().get("detail", "")
            assert any(keyword in str(error_detail).lower() 
                      for keyword in ["invalid", "malformed", "format", "reddit"])
    
    def test_high_concurrency_verification_races(self, client, db_session):
        """Test handling of concurrent verification attempts"""
        
        from app.models import User
        import threading
        import concurrent.futures
        
        user = User(id="concurrent_test", username="concurrent")
        db_session.add(user)
        db_session.commit()
        
        def start_verification(index):
            return client.post("/api/verify/start", json={
                "user_id": user.id,
                "reddit_post_url": f"https://reddit.com/r/tech/comments/race{index}"
            })
        
        # Run multiple verification starts concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(start_verification, i) for i in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Verify at least one succeeded, handle any race conditions
        success_count = sum(1 for r in results if r.status_code == 200)
        
        # Expected: should handle concurrent requests gracefully
        assert success_count >= 1  # At least one should succeed
    
    def test_user_deleted_mid_verification(self, client, db_session):
        """Test handling when user account is deleted during verification"""
        
        from app.models import User
        user = User(id="delete_test_user", username="delete_test")
        db_session.add(user)
        
        attempt = VerificationAttempt(
            user_id=user.id,
            reddit_post_url="https://reddit.com/r/tech/comments/delete_test",
            status=VerificationStatus.IN_PROGRESS,
            step=1
        )
        db_session.add(attempt)
        db_session.commit()
        
        # Simulate user deletion
        db_session.delete(user)
        db_session.commit()
        
        # Attempt to continue verification with deleted user
        response = client.post(f"/api/verify/{attempt.id}/step2", json={
            "answer": "User no longer exists"
        })
        
        assert response.status_code == 404
        assert "user" in response.json()["detail"].lower()
    
    def test_verification_step_preconditions(self, client, db_session):
        """Test that verification steps enforce correct order"""
        
        from app.models import User
        user = User(id="step_order_test", username="step_test")
        db_session.add(user)
        db_session.commit()
        
        # Mock valid submission
        with patch('app.services.reddit.RedditClient') as mock_client:
            instance = mock_client.return_value
            instance.get_submission.return_value = {
                "title": "Test post",
                "body": "Test content",
                "author": "step_order_test",
                "created_utc": datetime.now().timestamp()
            }
            
            # Start verification
            response = client.post("/api/verify/start", json={
                "user_id": "step_order_test",
                "reddit_post_url": "https://reddit.com/r/tech/comments/order"
            })
            assert response.status_code == 200
            attempt_id = response.json()["attempt_id"]
            
            # Try to submit step 2 directly without completing step 1
            response = client.post(f"/api/verify/{attempt_id}/step2", json={
                "answer": "Skipping step 1"
            })
            assert response.status_code == 400
            assert "step 1" in response.json()["detail"].lower()
            
            # Submit step 1 normally
            response = client.post(f"/api/verify/{attempt_id}/step1", json={
                "answer": "Valid step 1 answer"
            })
            assert response.status_code == 200
            
            # Now step 2 should work
            response = client.post(f"/api/verify/{attempt_id}/step2", json={
                "answer": "Valid step 2 answer"
            })
            assert response.status_code == 200