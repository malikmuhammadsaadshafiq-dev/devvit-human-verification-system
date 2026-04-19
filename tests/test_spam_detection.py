"""
Tests for spam detection features in the verification system.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models import VerificationAttempt, SpamDetectionResult
 from app.services.spamdetector import SpamDetector


class TestSpamDetection:
    """
    Test cases for spam detection in verification responses
    """
    
    def test_promotional_content_detection(self, client, db_session):
        """Test detection of promotional content in verification answers"""
        
        spam_answers = [
            "Check out my amazing product at buy-mine-now.com! 50% off!",
            "Visit our website for premium services, limited time offer!",
            "Make money fast with this secret method! Click here: link.com",
            "Buy followers cheap! $5 per 1000. Message me on Instagram @promo",
            "🔥HOT DEALS🔥 70% off everything! Don't miss out!"
        ]
        
        detector = SpamDetector()
        
        for answer in spam_answers:
            result = detector.analyze_text(answer)
            assert result.is_spam == True
            assert result.confidence_score > 0.7
            assert "promotional" in result.reason.lower()
    
    def test_spam_detection_flags_suspicious_urls(self, client, db_session):
        """Test detection of promotional URLs in responses"""
        
        spam_urls = [
            "Visit buyawesomeoffer.com for best deals",
            "Check my product at mega-growth.net",
            "Use this link: special-promo-link.org/affiliate",
            "Get services at cheapfollwers.store"
        ]
        
        detector = SpamDetector()
        
        for text in spam_urls:
            result = detector.analyze_text(text)
            assert result.is_spam == True
            assert "promotional url" in result.reason.lower()
    
    def test_spam_detection_with_patterns(self, client, db_session):
        """Test detection of spam patterns like excessive caps or emojis"""
        
        spam_patterns = [
            "MAKE MONEY TODAY!!! 100% GUARANTEED!!!",
            "🔥🔥🔥HOT DEALS🔥🔥🔥 DON'T MISS OUT!!!",
            "BEST PRICES EVER!!!!! 💰💰💰💰",
            "GUARANTEED FOLLOWERS 100% REAL OR MONEY BACK!!!"
        ]
        
        detector = SpamDetector()
        
        for text in spam_patterns:
            result = detector.analyze_text(text)
            assert result.is_spam == True
            assert any(keyword in result.reason.lower() 
                      for keyword in ["excessive", "spam pattern", "promotional"])
    
    def test_legitimate_content_not_flagged(self, client, db_session):
        """Test legitimate answers are not falsely flagged as spam"""
        
        legitimate_answers = [
            "I think the main issue is battery drain on these devices",
            "The technology works well but has some limitations in current generation",
            "Users expect dual camera functionality in modern smartphones",
            "I've been using this app for 3 months and it's stable",
            "The performance improvement is noticeable with recent updates"
        ]
        
        detector = SpamDetector()
        
        for answer in legitimate_answers:
            result = detector.analyze_text(answer)
            assert result.is_spam == False
            assert result.confidence_score < 0.3
    
    def test_spam_detection_blocks_verification(self, client, db_session, mock_reddit_client):
        """Test that spam detection blocks verification flow"""
        
        # Setup user and attempt
        from app.models import User
        user = User(id="test_user_123", username="test_user")
        db_session.add(user)
        db_session.commit()
        
        mock_reddit_client.get_submission.return_value = {
            "title": "Manual question",
            "body": "This is legitimate content",
            "author": "test_user",
            "created_utc": datetime.now().timestamp() - 3600
        }
        
        # Start verification
        response = client.post("/api/verify/start", json={
            "user_id": "test_user_123",
            "reddit_post_url": "https://reddit.com/r/tech/comments/test123"
        })
        assert response.status_code == 200
        attempt_id = response.json()["attempt_id"]
        
        # Submit spam content
        spam_response = "BUY MY PRODUCT NOW! amazingdeal.net 50% off!"
        
        response = client.post(f"/api/verify/{attempt_id}/step1", json={
            "answer": spam_response
        })
        
        assert response.status_code == 400
        response_json = response.json()
        assert "spam" in response_json["detail"].lower()
        assert "promotional" in response_json["detail"].lower()
    
    def test_spam_detection_multiple_submissions_fail(self, client, db_session):
        """Test that multiple spam submissions result in account restriction"""
        
        from app.models import User
        user = User(id="spam_user_456", username="spam_user", spam_strikes=0)
        db_session.add(user)
        db_session.commit()
        
        spam_detector = SpamDetector()
        
        # Simulate multiple spam attempts
        spam_texts = [
            "Buy now at cheapstuff.com!",
            "Limited time offer! Special deals!",
            "Free followers, direct message me!"
        ]
        
        spam_count = 0
        for text in spam_texts:
            result = spam_detector.analyze_text(text)
            if result.is_spam:
                user.spam_strikes += 1
                spam_count += 1
                
        db_session.commit()
        
        # After 3 spam strikes, user should be blocked
        assert user.spam_strikes >= 3
        
        # Verify user cannot start new verification
        response = client.post("/api/verify/start", json={
            "user_id": "spam_user_456",
            "reddit_post_url": "https://reddit.com/r/tech/comments/test123"
        })
        
        assert response.status_code == 403
        assert "spam" in response.json()["detail"].lower()
    
    def test_spam_detection_analytics_storage(self, client, db_session):
        """Test that spam detection results are properly logged"""
        
        spam_detector = SpamDetector()
        
        # Analyze spam text
        text = "Mega deals! Click here now!"
        result = spam_detector.analyze_text(text)
        
        # Store result
        spam_result = SpamDetectionResult(
            verification_attempt_id="test_attempt_id",
            text_content=text,
            is_spam=result.is_spam,
            confidence_score=result.confidence_score,
            reason=result.reason
        )
        
        db_session.add(spam_result)
        db_session.commit()
        
        # Verify it was stored correctly
        stored_result = db_session.query(SpamDetectionResult).filter_by(
            verification_attempt_id="test_attempt_id"
        ).first()
        
        assert stored_result is not None
        assert stored_result.is_spam == True
        assert stored_result.confidence_score > 0.5
        assert "promotional" in stored_result.reason.lower()