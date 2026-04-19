import httpx
import json
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

async def send_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """Send webhook notification to configured endpoint."""
    
    if not webhook_url:
        logger.warning("No webhook URL configured")
        return False
    
    # Ensure payload has required fields
    if "timestamp" not in payload:
        payload["timestamp"] = datetime.utcnow().isoformat()
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Devvit-Verification-Bot/1.0"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook sent successfully: {payload.get('action', 'unknown')}")
                return True
            else:
                logger.error(
                    f"Webhook failed with status {response.status_code}: {response.text}"
                )
                return False
                
    except Exception as e:
        logger.error(f"Webhook failed: {str(e)}")
        return False

def format_webhook_payload(action: str, **kwargs) -> Dict[str, Any]:
    """Format webhook payload consistently."""
    
    supported_actions = [
        "verification_started",
        "verification_completed",
        "verification_approved",
        "verification_rejected",
        "admin_approval_required",
        "config_updated",
        "question_set_updated"
    ]
    
    if action not in supported_actions:
        raise ValueError(f"Unsupported webhook action: {action}")
    
    payload = {
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "data": kwargs
    }
    
    return payload

async def send_batch_webhook(webhook_url: str, events: list) -> bool:
    """Send multiple webhook events in a single request."""
    
    if not webhook_url or not events:
        return False
    
    payload = {
        "action": "batch_update",
        "events": events,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Devvit-Verification-Bot/1.0"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Batch webhook failed: {str(e)}")
        return False