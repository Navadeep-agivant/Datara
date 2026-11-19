import pytest
from app.utils.pii_masker import mask_pii_text, mask_pii_dict

def test_mask_pii_text():
    text = "Contact John at john.doe@example.com or call +919876543210 for details."
    masked = mask_pii_text(text)
    assert "john.doe@example.com" not in masked
    assert "[EMAIL_MASKED]" in masked
    assert "+919876543210" not in masked
    assert "[PHONE_MASKED]" in masked

def test_mask_pii_dict():
    payload = {
        "user": "Alice",
        "email": "alice@corp.net",
        "contacts": ["call 1234567890", "safe_val"]
    }
    masked = mask_pii_dict(payload)
    assert masked["email"] == "[EMAIL_MASKED]"
    assert "[PHONE_MASKED]" in masked["contacts"][0]
    assert masked["contacts"][1] == "safe_val"
