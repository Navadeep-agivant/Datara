import re
from typing import Any, List, Dict

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
PHONE_REGEX = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}')

def mask_pii_text(text: str) -> str:
    """
    Masks emails and phone numbers in any string.
    """
    if not isinstance(text, str):
        return text
    # Mask emails first
    masked = EMAIL_REGEX.sub("[EMAIL_MASKED]", text)
    # Mask potential phone numbers (only if contains at least 7 digits)
    def phone_replacer(match):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) >= 7:
            return "[PHONE_MASKED]"
        return match.group(0)
    
    masked = PHONE_REGEX.sub(phone_replacer, masked)
    return masked

def mask_pii_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize dictionaries before passing to LLM context.
    """
    sanitized = {}
    for k, v in data.items():
        if isinstance(v, str):
            sanitized[k] = mask_pii_text(v)
        elif isinstance(v, dict):
            sanitized[k] = mask_pii_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [
                mask_pii_text(item) if isinstance(item, str)
                else mask_pii_dict(item) if isinstance(item, dict)
                else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized
