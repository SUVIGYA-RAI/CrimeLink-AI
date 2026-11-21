"""
Entity Extractor Service
-------------------------
Uses spaCy for NLP Named Entity Recognition (NER) and
regular expressions for Indian phone numbers and vehicle registrations.

Includes intelligent deduplication and cross-model entity resolution:
- Structured regexes (PHONE_NUMBER, VEHICLE_NUMBER) take precedence over general NLP.
- Overlapping fragments (e.g. spaCy tagging "MH" as ORG when part of vehicle MH 14 CD 7890,
  or tagging a 10-digit number as DATE) are automatically pruned.
- Repeated occurrences of the exact same entity in a document are consolidated to a single record.
"""

import re

# ── Regex Patterns ─────────────────────────────────────────────────────────────
# Indian mobile number: starts with 6-9, 10 digits, optionally prefixed +91 or 0
PHONE_REGEX   = re.compile(r'\b(?:\+91|0)?[6-9]\d{9}\b')

# Indian vehicle registration: e.g. MH 12 AB 1234, KA 01 MJ 4321
VEHICLE_REGEX = re.compile(r'\b[A-Z]{2}\s?\d{2}\s?[A-Z]{1,2}\s?\d{4}\b')


def _load_spacy():
    """
    Load the spaCy model. Returns None if spaCy is not installed,
    so the app still works (regex extraction still runs).
    """
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except ImportError:
        return None
    except OSError:
        return None


# Load once at module level (cached for the lifetime of the process)
_NLP = _load_spacy()


def extract_entities(text: str) -> list:
    """
    Extract entities from FIR text.
    Deduplicates repeated mentions and resolves cross-model conflicts.
    """
    # 1. First, extract structured entities with regex (high precision)
    regex_entities = []
    phone_matches = set()
    vehicle_matches = set()

    for match in PHONE_REGEX.finditer(text):
        val = match.group().strip()
        if val not in phone_matches:
            phone_matches.add(val)
            regex_entities.append({
                "text":       val,
                "type":       "PHONE_NUMBER",
                "method":     "regex",
                "confidence": 1.0,
            })

    for match in VEHICLE_REGEX.finditer(text):
        val = match.group().strip()
        if val not in vehicle_matches:
            vehicle_matches.add(val)
            regex_entities.append({
                "text":       val,
                "type":       "VEHICLE_NUMBER",
                "method":     "regex",
                "confidence": 1.0,
            })

    # 2. Extract spaCy NER entities
    spacy_entities = []
    if _NLP is not None:
        doc = _NLP(text)
        for ent in doc.ents:
            clean = ent.text.strip()
            # Ignore single character noise
            if len(clean) <= 1:
                continue

            # Skip if this text is a phone number already caught by regex
            if clean in phone_matches or any(clean in p for p in phone_matches):
                continue

            # Skip if this text is an artifact/fragment of a vehicle number (e.g. "MH", "3456")
            if any(clean in v for v in vehicle_matches):
                continue

            # We care about these spaCy labels:
            if ent.label_ in ('PERSON', 'ORG', 'GPE', 'LOC', 'DATE', 'TIME', 'MONEY', 'NORP', 'FAC'):
                spacy_entities.append({
                    "text":       clean,
                    "type":       ent.label_,
                    "method":     "spacy",
                    "confidence": 1.0,
                })

    # 3. Consolidate and deduplicate: regex first, then unique spaCy entities
    final_entities = list(regex_entities)
    seen_texts = {e["text"].lower() for e in regex_entities}

    for item in spacy_entities:
        key = item["text"].lower()
        if key not in seen_texts:
            seen_texts.add(key)
            final_entities.append(item)

    return final_entities
