"""
Input validation utilities for the Rideshare Bot.
Ensures data integrity and provides user-friendly error messages.
"""
import re
from typing import Tuple


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Validate user/driver name.
    
    Rules:
    - Length: 2-50 characters
    - Characters: Letters, spaces, hyphens, apostrophes
    
    Returns:
        (is_valid, error_message)
    """
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long."
    
    if len(name) > 50:
        return False, "Name must be less than 50 characters."
    
    # Allow letters (any language), spaces, hyphens, apostrophes
    if not re.match(r"^[\w\s\-']+$", name, re.UNICODE):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes."
    
    return True, ""


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Validate phone number (Ethiopian and international formats).
    
    Accepted formats:
    - +251XXXXXXXXX (Ethiopian international)
    - 09XXXXXXXX (Ethiopian local)
    - +XXXXXXXXXXX (Other international)
    
    Returns:
        (is_valid, error_message)
    """
    # Remove spaces, dashes, and parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    if not cleaned:
        return False, "Phone number cannot be empty."
    
    # Ethiopian format: +251 or 09
    if cleaned.startswith('+251'):
        if len(cleaned) != 13 or not cleaned[1:].isdigit():
            return False, "Ethiopian number must be +251XXXXXXXXX (13 digits total)."
        return True, ""
    
    if cleaned.startswith('09'):
        if len(cleaned) != 10 or not cleaned.isdigit():
            return False, "Ethiopian number must be 09XXXXXXXX (10 digits)."
        return True, ""
    
    if cleaned.startswith('07'):
        if len(cleaned) != 10 or not cleaned.isdigit():
            return False, "Ethiopian number must be 07XXXXXXXX (10 digits)."
        return True, ""
    
    # International format: +XX...
    if cleaned.startswith('+'):
        if len(cleaned) < 10 or len(cleaned) > 15 or not cleaned[1:].isdigit():
            return False, "International number must be +XXXXXXXXXX (10-15 digits)."
        return True, ""
    
    return False, "Please enter a valid phone number.\nExamples: +251912345678 or 0912345678"


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to international format.
    Converts 09XX to +251 9XX format.
    """
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    if cleaned.startswith('09') or cleaned.startswith('07'):
        return '+251' + cleaned[1:]
    
    return cleaned


def validate_rating(rating: int) -> Tuple[bool, str]:
    """
    Validate ride rating.
    
    Rules:
    - Must be integer between 1 and 5
    
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(rating, int):
        return False, "Rating must be a number."
    
    if rating < 1 or rating > 5:
        return False, "Rating must be between 1 and 5 stars."
    
    return True, ""


def validate_vehicle_type(vehicle_type: str, valid_types: list) -> Tuple[bool, str]:
    """
    Validate vehicle type against allowed types.
    
    Returns:
        (is_valid, error_message)
    """
    if vehicle_type not in valid_types:
        return False, f"Invalid vehicle type. Choose from: {', '.join(valid_types)}"
    
    return True, ""


def sanitize_input(text: str, max_length: int = 200) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    # Remove any control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Trim to max length
    text = text[:max_length]
    
    # Strip leading/trailing whitespace
    return text.strip()
