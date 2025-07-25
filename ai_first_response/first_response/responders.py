import google.generativeai as genai
from pydantic import BaseModel, ValidationError
from django.conf import settings
from django.utils.translation import gettext as _
import re

# 1) Configure your API Key
genai.configure(api_key=settings.GEMINI_API_KEY)

# 2) Define response schema
class GeminiResp(BaseModel):
    category: str
    severity: str
    instructions: list[str]

# 3) Language detection function
def detect_language(text: str) -> str:
    """Simple language detection based on common Italian words"""
    italian_words = [
        'aiuto', 'emergenza', 'terremoto', 'incendio', 'alluvione', 'medico', 'polizia',
        'sono', 'c\'è', 'ho', 'bisogno', 'di', 'nella', 'mia', 'zona', 'per', 'favore',
        'casa', 'famiglia', 'ferito', 'male', 'ospedale', 'ambulanza', 'fuoco', 'acqua'
    ]
    
    text_lower = text.lower()
    italian_count = sum(1 for word in italian_words if word in text_lower)
    
    # If more than 1 Italian word found, likely Italian
    return 'it' if italian_count > 1 else 'en'

# 4) Multilingual prompt templates
TEMPLATE_EN = """You are an emergency first-response assistant.
ALWAYS reply in EXACT JSON: {{"category":"...","severity":"...","instructions":["...","..."]}}
Provide instructions in ENGLISH.
User is at (lat:{lat},lon:{lon}). Context feed: {feed}

Severity levels: CRIT (life-threatening), HIGH (urgent), MED (moderate), LOW (minor), INFO (informational)
Categories: Earthquake, Fire, Medical, Flood, Police, Weather, Emergency, Unknown

User message: "{msg}"
"""

TEMPLATE_IT = """Sei un assistente per la risposta alle emergenze.
Rispondi SEMPRE in JSON ESATTO: {{"category":"...","severity":"...","instructions":["...","..."]}}
Fornisci le istruzioni in ITALIANO.
L'utente è alle coordinate (lat:{lat},lon:{lon}). Feed contestuale: {feed}

Livelli di gravità: CRIT (pericolo di vita), HIGH (urgente), MED (moderato), LOW (minore), INFO (informativo)
Categorie: Earthquake, Fire, Medical, Flood, Police, Weather, Emergency, Unknown

Messaggio utente: "{msg}"
"""

def classify_message(msg: str, lat: float, lon: float, feed: str = "", user_lang: str = None) -> dict:
    # Determine language to use
    if user_lang:
        # Use provided user language preference
        language = user_lang
    else:
        # Fallback to auto-detection
        language = detect_language(msg)
    
    # Select appropriate template
    template = TEMPLATE_IT if language == 'it' else TEMPLATE_EN
    
    prompt = template.format(msg=msg, lat=lat, lon=lon, feed=feed)
    try:
        # 4) Make chat completion with Gemini Flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                candidate_count=1,
            )
        )

        raw = response.text
        
        # Extract JSON from markdown block if present
        if "```json" in raw:
            # Find start and end of JSON block
            start = raw.find("```json") + 7  # +7 to skip "```json\n"
            end = raw.find("```", start)
            if end != -1:
                raw = raw[start:end].strip()
        
        parsed = GeminiResp.model_validate_json(raw)
        return parsed.model_dump()
    except ValidationError:
        # Return fallback in detected language
        fallback_msg = "Non sono sicuro, chiama il 112." if language == 'it' else "I'm not sure, please call 112."
        return {
            "category": "UNKNOWN",
            "severity": "INFO",
            "instructions": [fallback_msg]
        }
    except Exception as e:
        # Generic fallback in detected language
        if language == 'it':
            error_msg = f"Errore interno: {str(e)}"
        else:
            error_msg = f"Internal error: {str(e)}"
        
        return {
            "category": "ERROR",
            "severity": "CRIT",
            "instructions": [error_msg]
        }