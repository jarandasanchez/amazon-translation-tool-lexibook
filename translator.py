import re
import time
from typing import List, Callable, Optional
from openai import OpenAI


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


def get_translation_prompt(target_language: str) -> str:
    """
    Generate the translation prompt for a specific target language.
    """
    lang_name = LANGUAGE_NAMES.get(target_language, target_language)

    return f"""You are a highly skilled marketing and language expert specializing in accurately translating product-related content into {lang_name}.

Key Requirements:
- Translate all textual content exactly as provided
- Maintain original tone, style, and marketing nuances
- Preserve SKU numbers and product identifiers exactly as they appear (do not translate SKUs)
- Use consistent terminology throughout the dataset
- If the input is empty, null, or contains only whitespace, respond with a single hyphen (-)
- Provide only the final translated text without any preambles, explanations, or metadata

Output quality expectations:
- Flawless spelling and grammar in {lang_name}
- Natural-sounding translations that a native speaker would use
- Preserve any HTML tags, formatting markers, or special characters"""


def fix_lexibook_quality(text: str, target_language: str) -> str:
    """
    Fix 'Qualité Lexibook' translations to use correct language-specific versions.
    This handles the BP5 quality bullet point that needs special attention.
    """
    if target_language not in LEXIBOOK_QUALITY_TRANSLATIONS:
        return text

    correct_translation = LEXIBOOK_QUALITY_TRANSLATIONS[target_language]

    # Common incorrect variations to fix
    incorrect_variants = [
        "Qualité Lexibook",  # French left untranslated
        "Lexibook quality",  # lowercase
        "lexibook quality",
        "Qualité lexibook",
        "Quality Lexibook",
        "Lexibook Quality",  # might be wrong for non-EN
    ]

    # For non-English, also replace English version if it was left
    if target_language != "EN":
        for variant in incorrect_variants:
            if variant.lower() in text.lower():
                # Case-insensitive replace
                pattern = re.compile(re.escape(variant), re.IGNORECASE)
                text = pattern.sub(correct_translation, text)

    return text


def translate_single(
    text: str,
    target_language: str,
    client: OpenAI,
    model: str = "gpt-4o-mini",
    max_retries: int = 3
) -> str:
    """
    Translate a single text to the target language with retry logic.
    """
    if not text or str(text).strip() == "" or str(text).strip() == "-" or str(text).strip().lower() == "nan":
        return "-"

    prompt = get_translation_prompt(target_language)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": str(text)}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            translated = response.choices[0].message.content.strip()

            # Fix Lexibook quality translations (BP5)
            translated = fix_lexibook_quality(translated, target_language)

            return translated

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise Exception(f"Translation failed after {max_retries} attempts: {str(e)}")


def translate_content_list(
    content_list: List[str],
    target_language: str,
    client: OpenAI,
    model: str = "gpt-4o-mini",
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[str]:
    """
    Translate a list of content strings.

    Args:
        content_list: List of texts to translate
        target_language: Target language code (EN, ES, etc.)
        client: OpenAI client instance
        model: Model to use for translation
        progress_callback: Optional callback(current, total) for progress updates

    Returns:
        List of translated texts
    """
    translations = []
    total = len(content_list)

    for i, text in enumerate(content_list):
        translated = translate_single(str(text), target_language, client, model)
        translations.append(translated)

        if progress_callback:
            progress_callback(i + 1, total)

    return translations


def estimate_cost(content_list: List[str], num_languages: int) -> float:
    """
    Estimate translation cost in USD.
    GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
    """
    total_chars = sum(len(str(t)) for t in content_list)
    tokens = total_chars // 4
    input_cost = (tokens * num_languages) * 0.15 / 1_000_000
    output_cost = (tokens * num_languages) * 0.60 / 1_000_000
    return input_cost + output_cost
