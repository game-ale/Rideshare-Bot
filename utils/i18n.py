"""
i18n utility for the Rideshare Bot.
Handles message translation based on user language preference.
"""
import json
import os
from typing import Dict, Any
from utils.logger import logger

# Cache for translations
_translations: Dict[str, Dict[str, str]] = {}
LOCALES_DIR = "locales"

def load_translations():
    """Load all translation files from the locales directory."""
    global _translations
    try:
        for filename in os.listdir(LOCALES_DIR):
            if filename.endswith(".json"):
                lang_code = filename.split(".")[0]
                with open(os.path.join(LOCALES_DIR, filename), "r", encoding="utf-8") as f:
                    _translations[lang_code] = json.load(f)
        logger.info(f"Loaded translations for: {', '.join(_translations.keys())}")
    except Exception as e:
        logger.error(f"Failed to load translations: {e}")

def t(key: str, lang: str = "en", **kwargs) -> str:
    """
    Translate a string given a key and language code.
    Fallback to English if translation missing.
    """
    if not _translations:
        load_translations()
        
    lang_translations = _translations.get(lang, _translations.get("en", {}))
    template = lang_translations.get(key, _translations.get("en", {}).get(key, key))
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing format key {e} in translation '{key}' for '{lang}'")
        return template
    except Exception as e:
        logger.error(f"Translation error for '{key}': {e}")
        return template

def get_all_translations(key: str) -> list:
    """Get all translated values for a key across all languages."""
    values = []
    for lang in _translations:
        if key in _translations[lang]:
            values.append(_translations[lang][key])
    # Also add English explicitly if not already there (fallback)
    en_val = _translations.get("en", {}).get(key)
    if en_val and en_val not in values:
        values.append(en_val)
    return list(set(values))

# Initial load
load_translations()
