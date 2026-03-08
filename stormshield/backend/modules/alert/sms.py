"""
SMS utility for StormShield AI using 2Factor.in
"""
import httpx
import logging
import urllib.parse
from backend.config import settings

logger = logging.getLogger(__name__)

def _get_api_key() -> str | None:
    """Helper to get 2Factor API key."""
    api_key = getattr(settings, "two_factor_api_key", None)
    if not api_key:
        import os
        api_key = os.getenv("TWO_FACTOR_API_KEY")
    return api_key

def _sanitize_phone(phone: str) -> str:
    """Remove non-numeric characters from phone number."""
    return "".join(filter(str.isdigit, phone))

def send_sms_alert(phone_number: str, message: str) -> bool:
    """Send an SMS alert via 2Factor.in transactional API."""
    api_key = _get_api_key()
    phone = _sanitize_phone(phone_number)
    
    if not api_key:
        logger.warning("TWO_FACTOR_API_KEY not set. SMS not sent.")
        return False
        
    # URL encoded message is required for 2Factor
    encoded_msg = urllib.parse.quote(message)
    url = f"https://2factor.in/API/V1/{api_key}/SMS/{phone}/{encoded_msg}"
    
    try:
        resp = httpx.get(url, timeout=12)
        resp.raise_for_status()
        result = resp.json()
        if result.get("Status") == "Success":
            logger.info(f"SMS sent to {phone_number} successfully. ID: {result.get('Details')}")
            return True
        else:
            logger.error(f"2Factor API error for {phone_number}: {result}")
            return False
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {e}")
        return False

def send_otp(phone_number: str) -> str | None:
    """Trigger an OTP via 2Factor. Returns session_id if successful."""
    api_key = _get_api_key()
    phone = _sanitize_phone(phone_number)
    if not api_key:
        return None
    
    url = f"https://2factor.in/API/V1/{api_key}/SMS/{phone}/AUTOGEN"
    try:
        resp = httpx.get(url, timeout=12)
        resp.raise_for_status()
        result = resp.json()
        if result.get("Status") == "Success":
            return result.get("Details") # This is the session_id
        return None
    except Exception as e:
        logger.error(f"OTP send failed for {phone_number}: {e}")
        return None

def verify_otp(session_id: str, otp: str) -> bool:
    """Verify an OTP session."""
    api_key = _get_api_key()
    if not api_key:
        return False
    
    url = f"https://2factor.in/API/V1/{api_key}/SMS/VERIFY/{session_id}/{otp}"
    try:
        resp = httpx.get(url, timeout=12)
        resp.raise_for_status()
        result = resp.json()
        logger.info(f"OTP verification response: {result}")
        
        details = result.get("Details", "").lower()
        if result.get("Status") == "Success" and ("matched" in details or "success" in details):
            return True
        return False
    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        return False

def broadcast_alert(message: str, subscribers: list[str]):
    """Broadcast an alert message to all subscribers."""
    if not subscribers:
        return
    
    logger.info(f"Broadcasting alert to {len(subscribers)} subscribers.")
    for phone in subscribers:
        send_sms_alert(phone, message)
