from typing import List, Optional
import logging
import os
import time
from openai import OpenAI

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError(" No OpenAI API key found. ")

client = OpenAI(api_key=OPENAI_API_KEY)


def translate_to_english(text: str, source_language: Optional[str] = None, model: str = "gpt-4o-mini") -> str:
    """
    Translate text to English using OpenAI LLM.
    Returns original text on error or if input is empty.
    """
    if not text or not str(text).strip():
        return text

    try:
        system_prompt = (
            "You are a concise translator. Translate the user's text into natural, fluent English. "
            "Return only the translated text with no extra commentary."
        )
        user_prompt = f"Translate the following text to English. Source language hint: {source_language or 'unknown'}.\n\n{text}"

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2000,
            temperature=0.0,
        )

        return resp.choices[0].message.content.strip()

    except Exception as e:
        logger.exception(f"OpenAI translation failed: {e}")
        return text


def batch_translate(texts: List[str], source_language: Optional[str] = None, delay: float = 0.0) -> List[str]:
    """
    Translate a list of texts to English using translate_to_english.
    Returns translated strings in the same order. Original text is kept if translation fails.
    """
    if not texts:
        return []

    results: List[str] = []
    for t in texts:
        try:
            translated = translate_to_english(t, source_language=source_language)
            results.append(translated)
        except Exception as e:
            logger.exception(f"Per-item translation failed: {e}")
            results.append(t)

        if delay > 0:
            time.sleep(delay)

    return results
