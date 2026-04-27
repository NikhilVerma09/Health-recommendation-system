import requests
import os

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

def transcribe_audio(file_path: str, language_code: str = "hi-IN"):
    """
    Transcribe audio using Sarvam AI Speech-to-Text API
    
    Args:
        file_path: Path to the audio file (WAV or MP3)
        language_code: Language code (default: hi-IN for Hindi)
                      Supported: hi-IN, en-IN, bn-IN, kn-IN, ml-IN, 
                                mr-IN, od-IN, pa-IN, ta-IN, te-IN, gu-IN
    
    Returns:
        tuple: (transcript_text, detected_language_code)
    """
    url = "https://api.sarvam.ai/speech-to-text"
    
    
    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }
    
    with open(file_path, 'rb') as audio_file:
        # Determine file type
        file_extension = file_path.lower().split('.')[-1]
        mime_type = 'audio/wav' if file_extension == 'wav' else 'audio/mpeg'
        
        files = {
            'file': (f'audio.{file_extension}', audio_file, mime_type)
        }
        
        data = {
            'model': 'saarika:v2.5',  # Latest Sarvam STT model
            'language_code': language_code
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        result = response.json()
    
    return result.get("transcript", ""), result.get("language_code", "unknown")