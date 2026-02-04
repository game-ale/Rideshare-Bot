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
