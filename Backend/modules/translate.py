import requests
import os

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

def translate_to_english(text: str, source_lang: str = "hi-IN"):
    """
    Translate text to English using Sarvam AI Translation API
    
    Args:
        text: Text to translate
        source_lang: Source language code (default: hi-IN for Hindi)
    
    Returns:
        str: Translated text in English
    """
    url = "https://api.sarvam.ai/translate"
    
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": text,
        "source_language_code": source_lang,
        "target_language_code": "en-IN",
        "speaker_gender": "Male",
        "mode": "formal",
        "model": "mayura:v1",
        "enable_preprocessing": True
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    
    return result.get("translated_text", text)