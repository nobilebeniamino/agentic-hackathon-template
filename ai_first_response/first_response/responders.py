import google.generativeai as genai
from pydantic import BaseModel, ValidationError
from django.conf import settings
from django.utils.translation import gettext as _

# 1) Configure your API Key
genai.configure(api_key=settings.GEMINI_API_KEY)

# 2) Define response schema
class GeminiResp(BaseModel):
    category: str
    severity: str
    instructions: list[str]

# 3) Prompt template
TEMPLATE = """You are an emergency first-response assistant.
ALWAYS reply in EXACT JSON: {{"category":"...","severity":"...","instructions":["...","..."]}}
User is at (lat:{lat},lon:{lon}). Context feed: {feed}

User message: "{msg}"
"""

def classify_message(msg: str, lat: float, lon: float, feed: str = "") -> dict:
    prompt = TEMPLATE.format(msg=msg, lat=lat, lon=lon, feed=feed)
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
        return {
            "category": "UNKNOWN",
            "severity": "INFO",
            "instructions": [_("I'm not sure, please call 112.")]
        }
    except Exception as e:
        # Generic fallback
        return {
            "category": "ERROR",
            "severity": "CRIT",
            "instructions": [_("Internal error: %(error)s") % {"error": str(e)}]
        }