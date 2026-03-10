"""
Glossary system for consistent translation of brand terms and character names.
Supports a built-in default glossary and optional CSV upload for custom terms.
Editable via the Glossary page — saved to glossary_data.json.
"""
import csv
import io
import json
import os
from typing import Dict, List, Optional

GLOSSARY_FILE = os.path.join(os.path.dirname(__file__), "glossary_data.json")


# Brand terms with per-language translations
DEFAULT_GLOSSARY: List[Dict[str, str]] = [
    {
        "term": "Qualité Lexibook",
        "EN": "Lexibook Quality",
        "FR": "Qualité Lexibook",
        "ES": "Calidad Lexibook",
        "IT": "Qualità Lexibook",
        "DE": "Lexibook Qualität",
        "NL": "Lexibook Kwaliteit",
        "PL": "Jakość Lexibook",
        "SE": "Lexibook Kvalitet",
    },
]

# Official license name translations (from Licence_Name.xlsx)
# These ensure license/franchise names are always translated correctly
LICENSE_NAMES: List[Dict[str, str]] = [
    {"term": "Le Roi Lion", "FR": "Le Roi Lion", "EN": "The Lion King", "ES": "El rey león", "IT": "Il re leone", "DE": "Der König der Löwen", "NL": "De Leeuwenkoning", "PL": "Król Lew", "SE": "Lejonkungen"},
    {"term": "Moi, moche et méchant", "FR": "Moi, moche et méchant", "EN": "Despicable Me", "ES": "Mi villano favorito", "IT": "Cattivissimo me", "DE": "Ich - Einfach unverbesserlich", "NL": "Despicable Me", "PL": "Minionkami", "SE": "Dumma mej"},
    {"term": "Princesses Disney", "FR": "Princesses Disney", "EN": "Disney Princess", "ES": "Princessas Disney", "IT": "Principesse Disney", "DE": "Disney Prinzessin", "NL": "Disneyprinses", "PL": "Disney Princess", "SE": "Disneyprinsessor"},
    {"term": "La Reine des Neiges", "FR": "La Reine des Neiges", "EN": "Frozen", "ES": "Frozen", "IT": "Frozen", "DE": "Die Eiskönigin", "NL": "Frozen", "PL": "Kraina Lodu", "SE": "Frost"},
    {"term": "Gabby et la Maison Magique", "FR": "Gabby et la Maison Magique", "EN": "Gabby's Dollhouse", "ES": "La Casa de Muñecas de Gabby", "IT": "La Casa delle Bambole di Gabby", "DE": "Gabby's Dollhouse", "NL": "Gabby's Dollhouse", "PL": "Koci domek Gabi", "SE": "Gabbys dockskåp"},
    {"term": "Les Gardiens de la Galaxie", "FR": "Les Gardiens de la Galaxie", "EN": "Guardians of the Galaxy", "ES": "Guardianes de la Galaxia", "IT": "Guardiani della Galassia", "DE": "Guardians of the Galaxy", "NL": "Guardians of the Galaxy", "PL": "Strażnicy Galaktyki", "SE": "Guardians of the Galaxy"},
    {"term": "La Pat' Patrouille", "FR": "La Pat' Patrouille", "EN": "Paw Patrol", "ES": "La Patrulla Canina", "IT": "Paw Patrol", "DE": "Paw Patrol", "NL": "Paw Patrol", "PL": "Psi Patrol", "SE": "Paw Patrol"},
    {"term": "Les Schtroumpfs", "FR": "Les Schtroumpfs", "EN": "The Smurfs", "ES": "Los Pitufos", "IT": "Puffi", "DE": "Die Schlümpfe", "NL": "De Smurfen", "PL": "Smerfy", "SE": "Smurfarna"},
    {"term": "Spidey et ses amis extraordinaires", "FR": "Spidey et ses amis extraordinaires", "EN": "Spidey and His Amazing Friends", "ES": "Spidey y su superequipo", "IT": "Spidey e i suoi fantastici amici", "DE": "Spidey und seine Super-Freunde", "NL": "Spidey and His Amazing Friends", "PL": "Spidey i super-kumple", "SE": "Spidey and His Amazing Friends"},
    {"term": "Buzz l'Eclair", "FR": "Buzz l'Eclair", "EN": "Buzz Lightyear", "ES": "Buzz Lightyear", "IT": "Buzz Lightyear", "DE": "Buzz Lightyear", "NL": "Buzz Lightyear", "PL": "Buzz Astral", "SE": "Lightyear"},
    {"term": "Mickey Mouse", "FR": "Mickey Mouse", "EN": "Mickey Mouse", "ES": "Mickey Mouse", "IT": "Mickey Mouse", "DE": "Mickey Mouse", "NL": "Mickey Mouse", "PL": "Myszka Miki", "SE": "Musse Pigg"},
    {"term": "Minnie Mouse", "FR": "Minnie Mouse", "EN": "Minnie Mouse", "ES": "Minnie Mouse", "IT": "Minnie Mouse", "DE": "Minnie Mouse", "NL": "Minnie Mouse", "PL": "Myszka Minnie", "SE": "Mimmi Pigg"},
    {"term": "Miraculous Ladybug Chat Noir", "FR": "Miraculous Ladybug Chat Noir", "EN": "Miraculous Ladybug Cat Noir", "ES": "Miraculous Ladybug Cat Noir", "IT": "Miraculous Ladybug Chat Noir", "DE": "Miraculous Ladybug Cat Noir", "NL": "Miraculous Ladybug Cat Noir", "PL": "Miraculum Biedronka Czarny Kot", "SE": "Miraculous Ladybug Cat Noir"},
    {"term": "Peppa Pig", "FR": "Peppa Pig", "EN": "Peppa Pig", "ES": "Peppa Pig", "IT": "Peppa Pig", "DE": "Peppa Wutz", "NL": "Peppa Pig", "PL": "Świnka Peppa", "SE": "Greta Gris"},
    {"term": "Les Vengadores", "FR": "The Avengers", "EN": "The Avengers", "ES": "Los Vengadores", "IT": "The Avengers", "DE": "The Avengers", "NL": "The Avengers", "PL": "The Avengers", "SE": "The Avengers"},
    {"term": "Football", "FR": "Football", "EN": "Soccer", "ES": "Fútbol", "IT": "Calcio", "DE": "Fußball", "NL": "Voetbal", "PL": "Piłka nożna", "SE": "Fotboll"},
    {"term": "Licorne", "FR": "Licorne", "EN": "Unicorn", "ES": "Unicornio", "IT": "Unicorno", "DE": "Einhorn", "NL": "Eenhoorn", "PL": "Jednorożec", "SE": "Enhörning"},
    {"term": "Dinosaure", "FR": "Dinosaure", "EN": "Dinosaur", "ES": "Dinosaurio", "IT": "Dinosauro", "DE": "Dinosaurier", "NL": "Dinosaurus", "PL": "Dinozaur", "SE": "Dinosaurier"},
    {"term": "Chaton", "FR": "Chaton", "EN": "Kitty", "ES": "Gatito", "IT": "Gattino", "DE": "Kitty", "NL": "Kitty", "PL": "Koteczek", "SE": "Kattunge"},
    {"term": "Ours Polaire", "FR": "Ours Polaire", "EN": "Polar Bear", "ES": "Oso Polar", "IT": "Orso Polare", "DE": "Eisbär", "NL": "Ijsbeer", "PL": "Niedźwiedź Polarny", "SE": "Isbjörn"},
    {"term": "Fusée", "FR": "Fusée", "EN": "Rocket", "ES": "Cohete", "IT": "Razzo", "DE": "Rakete", "NL": "Raket", "PL": "Rakieta", "SE": "Raket"},
    {"term": "Noir", "FR": "Noir", "EN": "Black", "ES": "Negro", "IT": "Nero", "DE": "Schwarz", "NL": "Zwart", "PL": "Czarny", "SE": "Svart"},
    {"term": "Animal", "FR": "Animal", "EN": "Animals", "ES": "Animales", "IT": "Animali", "DE": "Tiere", "NL": "Dieren", "PL": "Zwierzętami", "SE": "Djur"},
    {"term": "Basketball", "FR": "Basketball", "EN": "Basketball", "ES": "Basketball", "IT": "Basketball", "DE": "Basketball", "NL": "Basketball", "PL": "Koszykówka", "SE": "Basketboll"},
    {"term": "Idéfix", "FR": "Idéfix", "EN": "Dogmatix", "ES": "Ideafix", "IT": "Idefix", "DE": "Idefix", "NL": "Idefix", "PL": "Idefiks", "SE": "Idefix"},
    {"term": "Astérix", "FR": "Astérix", "EN": "Asterix", "ES": "Asterix", "IT": "Asterix", "DE": "Asterix", "NL": "Asterix", "PL": "Asteriks", "SE": "Asterix"},
    {"term": "Hedwige", "FR": "Hedwige", "EN": "Hedwig", "ES": "Hedwig", "IT": "Edvige", "DE": "Hedwig", "NL": "Hedwig", "PL": "Hedwiga", "SE": "Hedwig"},
    {"term": "Vaiana", "FR": "Vaiana", "EN": "Moana", "ES": "Moana", "IT": "Oceania", "DE": "Vaiana", "NL": "Vaiana", "PL": "Vaiana", "SE": "Vaiana"},
    {"term": "Tom&Jerry", "FR": "Tom&Jerry", "EN": "Tom&Jerry", "ES": "Tom y Jerry", "IT": "Tom&Jerry", "DE": "Tom und Jerry", "NL": "Tom&Jerry", "PL": "Tom i Jerry", "SE": "Tom och Jerry"},
    {"term": "Pyjamask", "FR": "Pyjamask", "EN": "PJ Masks", "ES": "PJ Masks", "IT": "PJ Masks", "DE": "PJ Masks", "NL": "PJ Masks", "PL": "Pidżamersi", "SE": "Pyjamashjältarna"},
    {"term": "Baby Shark", "FR": "Baby Shark", "EN": "Baby Shark", "ES": "Baby Shark", "IT": "Baby Shark", "DE": "Baby Shark", "NL": "Baby Shark", "PL": "Baby Shark", "SE": "Hajarna"},
    {"term": "Cars", "FR": "Cars", "EN": "Cars", "ES": "Cars", "IT": "Cars", "DE": "Cars", "NL": "Cars", "PL": "Auta", "SE": "Bilar"},
    {"term": "Girafe", "FR": "Girafe", "EN": "Giraffe", "ES": "Jirafa", "IT": "Giraffa", "DE": "Giraffe", "NL": "Giraffe", "PL": "Żyrafa", "SE": "Giraff"},
    {"term": "Barbie", "FR": "Barbie", "EN": "Barbie", "ES": "Barbie", "IT": "Barbie", "DE": "Barbie", "NL": "Barbie", "PL": "Barbie", "SE": "Barbiedocka"},
]


def load_glossary_csv(file_content: bytes) -> List[Dict[str, str]]:
    """
    Parse a CSV file with glossary terms.
    Expected columns: term, EN, FR, ES, IT, DE, NL, PL, SE
    Returns list of term dicts (same format as DEFAULT_GLOSSARY).
    """
    text = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    entries = []
    for row in reader:
        if "term" in row and row["term"].strip():
            entries.append({k.strip(): v.strip() for k, v in row.items() if v})
    return entries


def format_glossary_for_prompt(
    glossary: List[Dict[str, str]],
    source_lang: str,
    target_lang: str,
) -> str:
    """
    Format glossary entries for injection into the translation prompt.
    Only includes entries that have both source and target language translations.
    """
    lines = []

    # Glossary term mappings
    term_lines = []
    for entry in glossary:
        src = entry.get(source_lang)
        tgt = entry.get(target_lang)
        if src and tgt:
            term_lines.append(f'  "{src}" -> "{tgt}"')

    if term_lines:
        lines.append("GLOSSARY — use these exact translations:")
        lines.extend(term_lines)

    return "\n".join(lines)


def _load_saved_glossary() -> Optional[List[Dict[str, str]]]:
    """Load glossary from JSON file if it exists."""
    if os.path.exists(GLOSSARY_FILE):
        try:
            with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def get_active_glossary(custom_entries: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """
    Load glossary: saved JSON > defaults. Merge with optional custom entries.
    """
    saved = _load_saved_glossary()
    glossary = saved if saved is not None else list(DEFAULT_GLOSSARY) + list(LICENSE_NAMES)

    if custom_entries:
        existing_terms = {e["term"].lower() for e in glossary}
        for entry in custom_entries:
            term_lower = entry.get("term", "").lower()
            if term_lower in existing_terms:
                glossary = [e for e in glossary if e["term"].lower() != term_lower]
            glossary.append(entry)
    return glossary
