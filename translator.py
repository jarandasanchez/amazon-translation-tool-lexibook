import re
import json
import time
import logging
from typing import List, Callable, Optional, Dict

from google import genai
from google.genai import types

from glossary import format_glossary_for_prompt, get_active_glossary


logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash"
MAX_BATCH_ROWS = 20

LANGUAGE_NAMES = {
    "EN": "English",
    "ES": "Spanish",
    "IT": "Italian",
    "DE": "German",
    "NL": "Dutch",
    "PL": "Polish",
    "SE": "Swedish",
    "FR": "French",
}

# Correct translations for "Qualité Lexibook" (BP5 quality bullet point)
LEXIBOOK_QUALITY_TRANSLATIONS = {
    "EN": "Lexibook Quality",
    "ES": "Calidad Lexibook",
    "IT": "Qualità Lexibook",
    "DE": "Lexibook Qualität",
    "NL": "Lexibook Kwaliteit",
    "PL": "Jakość Lexibook",
    "SE": "Lexibook Kvalitet",
    "FR": "Qualité Lexibook",
}


def detect_row_type(text: str) -> str:
    """Detect the type of content row for better prompt context."""
    text_lower = str(text).lower().strip()
    if not text_lower:
        return "general"
    # Check for common Amazon listing field patterns
    if any(kw in text_lower for kw in ["product name", "product_name", "titre", "title"]):
        return "product_name"
    if any(kw in text_lower for kw in ["bullet point", "bullet_point", "point fort"]):
        return "bullet_point"
    if any(kw in text_lower for kw in ["description", "product description"]):
        return "description"
    if any(kw in text_lower for kw in ["keyword", "generic keyword", "mot-clé", "mot clé", "search term"]):
        return "keywords"
    # Heuristic: semicolon-separated lists are likely keywords
    if ";" in str(text) and str(text).count(";") >= 3:
        return "keywords"
    # Heuristic: ALL CAPS text is likely a header/title
    if str(text) == str(text).upper() and len(str(text)) > 10:
        return "bullet_point"
    return "general"


def get_batch_prompt(source_lang: str, target_lang: str, glossary_section: str) -> str:
    """Generate the system prompt for batch JSON translation."""
    lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)

    return f"""You are translating Amazon product content from {source_name} to {lang_name}.

CRITICAL RULES:
1. Translate ALL text including UPPERCASE headers. "UNIVERSEL" in French → "UNIVERSELL" in German, "UNIVERSALE" in Italian, etc.
2. For semicolon-separated keyword lists: translate EVERY keyword phrase completely. Do not leave any phrase in the source language.
3. Use natural, modern vocabulary — avoid archaic or uncommon words.
4. Preserve: SKUs, brand names (Lexibook, Snoopy, Peanuts, Disney), model numbers, technical specs (watts, mAh, dimensions).
5. Do NOT add explanations. Return ONLY the JSON with translations.
6. If a source text is empty or contains only whitespace, return an empty string for that index.

{glossary_section}

You will receive a JSON object with rows to translate. Each row has an index, type (product_name, bullet_point, description, keywords, general), and text.

Respond with valid JSON only, in this exact format:
{{"translations": [{{"index": 0, "text": "translated text"}}, ...]}}"""


def fix_lexibook_quality(text: str, target_language: str) -> str:
    """Fix 'Qualité Lexibook' translations to use correct language-specific versions."""
    if target_language not in LEXIBOOK_QUALITY_TRANSLATIONS:
        return text

    correct_translation = LEXIBOOK_QUALITY_TRANSLATIONS[target_language]

    incorrect_variants = [
        "Qualité Lexibook",
        "Lexibook quality",
        "lexibook quality",
        "Qualité lexibook",
        "Quality Lexibook",
        "Lexibook Quality",
    ]

    if target_language != "EN":
        for variant in incorrect_variants:
            if variant.lower() in text.lower():
                pattern = re.compile(re.escape(variant), re.IGNORECASE)
                text = pattern.sub(correct_translation, text)

    return text


def translate_batch(
    rows: List[Dict],
    source_lang: str,
    target_lang: str,
    client: genai.Client,
    glossary_section: str,
    max_retries: int = 3,
) -> Dict[int, str]:
    """
    Translate a batch of rows via Gemini with JSON mode.
    Returns dict mapping index → translated text.
    """
    prompt = get_batch_prompt(source_lang, target_lang, glossary_section)

    payload = {
        "source_language": source_lang,
        "target_language": target_lang,
        "rows": rows,
    }

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=json.dumps(payload, ensure_ascii=False),
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.2,
                    max_output_tokens=16000,
                    response_mime_type="application/json",
                ),
            )

            raw = response.text.strip()
            logger.info(f"Batch {source_lang}→{target_lang} ({len(rows)} rows): got {len(raw)} chars")

            parsed = json.loads(raw)
            translations = parsed.get("translations", [])

            result = {}
            for item in translations:
                idx = item.get("index")
                text = item.get("text", "")
                if idx is not None:
                    text = fix_lexibook_quality(text, target_lang)
                    result[idx] = text

            # Verify we got all indices back
            expected = {r["index"] for r in rows}
            missing = expected - set(result.keys())
            if missing:
                logger.warning(f"Missing indices in batch response: {missing}")
                # Fill missing with empty to avoid silent gaps
                for idx in missing:
                    result[idx] = ""

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"JSON parse failed after {max_retries} attempts, falling back to cell-by-cell")
                return {}  # Signal to caller to fall back

        except Exception as e:
            logger.warning(f"Batch translation error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Batch translation failed after {max_retries} attempts: {e}")
                return {}

    return {}


def translate_single(
    text: str,
    source_lang: str,
    target_lang: str,
    client: genai.Client,
    glossary_section: str,
    max_retries: int = 3,
) -> str:
    """Translate a single text string (fallback for when batch fails)."""
    if not text or str(text).strip() == "" or str(text).strip() == "-" or str(text).strip().lower() == "nan":
        return ""

    lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)

    prompt = f"""Translate the following text from {source_name} to {lang_name}.
Translate ALL text including UPPERCASE words. Use modern, natural vocabulary.
Preserve brand names, SKUs, model numbers, and technical specs.
Return ONLY the translated text, nothing else.

{glossary_section}"""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=str(text),
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.2,
                    max_output_tokens=4000,
                ),
            )

            translated = response.text.strip()
            if not translated:
                logger.warning(f"Empty response for text: {text[:50]}...")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return ""

            translated = fix_lexibook_quality(translated, target_lang)
            logger.info(f"Single translate {source_lang}→{target_lang}: '{text[:30]}...' → '{translated[:30]}...'")
            return translated

        except Exception as e:
            logger.warning(f"Single translation error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Single translation failed after {max_retries} attempts: {e}")
                raise

    return ""


def translate_content_list(
    content_list: List[str],
    source_lang: str,
    target_lang: str,
    client: genai.Client,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    existing_content: Optional[dict] = None,
    custom_glossary: Optional[list] = None,
) -> List[str]:
    """
    Translate a list of content strings using batch JSON mode.
    Falls back to cell-by-cell if batch fails.
    """
    total = len(content_list)
    existing = existing_content or {}
    translations = [""] * total

    # Pre-fill existing content
    for i in range(total):
        if i in existing and existing[i].strip():
            translations[i] = existing[i]

    # Build glossary section for prompt
    glossary = get_active_glossary(custom_glossary)
    glossary_section = format_glossary_for_prompt(glossary, source_lang, target_lang)

    # Collect rows that need translation
    rows_to_translate = []
    for i, text in enumerate(content_list):
        if i in existing and existing[i].strip():
            continue  # Skip already-translated
        text_str = str(text).strip()
        if not text_str or text_str == "-" or text_str.lower() == "nan":
            translations[i] = ""
            continue
        rows_to_translate.append({
            "index": i,
            "type": detect_row_type(text_str),
            "text": text_str,
        })

    if not rows_to_translate:
        if progress_callback:
            progress_callback(total, total)
        return translations

    # Split into batches
    batches = [
        rows_to_translate[i:i + MAX_BATCH_ROWS]
        for i in range(0, len(rows_to_translate), MAX_BATCH_ROWS)
    ]

    translated_count = total - len(rows_to_translate)  # Already-filled count

    for batch_idx, batch in enumerate(batches):
        result = translate_batch(batch, source_lang, target_lang, client, glossary_section)

        if result:
            # Batch succeeded
            for row in batch:
                idx = row["index"]
                translations[idx] = result.get(idx, "")
                translated_count += 1
                if progress_callback:
                    progress_callback(translated_count, total)
        else:
            # Batch failed — fall back to cell-by-cell
            logger.warning(f"Batch {batch_idx+1} failed, falling back to cell-by-cell for {len(batch)} rows")
            for row in batch:
                idx = row["index"]
                try:
                    translations[idx] = translate_single(
                        row["text"], source_lang, target_lang, client, glossary_section
                    )
                except Exception as e:
                    logger.error(f"Cell-by-cell fallback failed for row {idx}: {e}")
                    translations[idx] = ""
                translated_count += 1
                if progress_callback:
                    progress_callback(translated_count, total)

    return translations


def estimate_cost(content_list: List[str], num_languages: int) -> float:
    """
    Estimate translation cost in USD.
    Gemini 2.5 Flash: $0.15 per 1M input tokens, $0.60 per 1M output tokens
    """
    total_chars = sum(len(str(t)) for t in content_list)
    tokens = total_chars // 4
    input_cost = (tokens * num_languages) * 0.15 / 1_000_000
    output_cost = (tokens * num_languages) * 0.60 / 1_000_000
    return input_cost + output_cost
