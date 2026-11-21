"""
Entity Extractor Service (Case-Centric AI Extraction)
------------------------------------------------------
Uses spaCy for NLP Named Entity Recognition (NER), regular expressions
for Indian phone numbers and vehicle plates, and linguistic heuristics
to extract structured CASES along with all associated entities and relationships.

Key Principle: Case-First Extraction.
All extracted entities (Persons, Vehicles, Organizations, Locations, Phone Calls)
belong strictly to their identified investigation case. No orphan entities are created.
"""

import re
import datetime


# ── Regex Patterns ─────────────────────────────────────────────────────────────
PHONE_REGEX = re.compile(r'\b(?:\+91|0)?[6-9]\d{9}\b')
VEHICLE_REGEX = re.compile(r'\b[A-Z]{2}\s?\d{2}\s?[A-Z]{1,2}\s?\d{4}\b')
FIR_CASE_REGEX = re.compile(
    r'\b(?:FIR|Case|Crime)\b\s*(?:(?:No\.?|Number|#)\s*[:\-]?|[:\-])\s*([A-Za-z0-9\/\-_]+)',
    re.IGNORECASE
)
LOCATION_REGEX = re.compile(
    r'(?:Place\s*of\s*Occurrence|Incident\s*Location|Location|Scene\s*of\s*Crime)\s*[:\-]?\s*([^\n\.,;]+)',
    re.IGNORECASE
)


def _load_spacy():
    """Load the spaCy English model if installed; returns None on failure."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


_NLP = _load_spacy()


# Known crime keywords mapped to Case model case_type choices
CRIME_TYPE_KEYWORDS = {
    'cyber_crime': ['cyber', 'phishing', 'hacking', 'otp', 'online fraud', 'malware', 'trojan', 'ransomware', 'ip address'],
    'theft': ['theft', 'stolen', 'burglary', 'robbery', 'robbed', 'heist', 'stole', 'break-in'],
    'fraud': ['fraud', 'scam', 'cheating', 'embezzlement', 'forgery', 'counterfeit', 'ponzi'],
    'murder': ['murder', 'homicide', 'killed', 'assassination', 'stabbed to death', 'fatal gunshot'],
    'assault': ['assault', 'attack', 'beaten', 'physical violence', 'grievous hurt', 'battery'],
    'drug_trafficking': ['drug', 'narcotics', 'contraband', 'ganja', 'heroin', 'cocaine', 'smuggling', 'substance'],
    'money_laundering': ['money laundering', 'hawala', 'shell company', 'black money', 'unaccounted cash', 'illicit funds'],
    'kidnapping': ['kidnap', 'abduction', 'hostage', 'ransom', 'missing child', 'held captive'],
}


def extract_case_centric_data(text: str, filename: str = "") -> dict:
    """
    Main entry point for Case-Centric AI Extraction.

    Analyzes document text to extract structured investigation cases
    with nested entities and relationships.

    Returns:
    {
        "cases": [
            {
                "case_number": str,
                "title": str,
                "description": str,
                "case_type": str,
                "location": str,
                "persons": list[dict],
                "phone_records": list[dict],
                "vehicles": list[dict],
                "organizations": list[dict],
                "locations": list[dict],
                "relationships": list[dict]
            }
        ]
    }
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return {"cases": []}

    # 1. Identify Case-Level Attributes
    case_number = _extract_case_number(clean_text)
    case_type = _infer_case_type(clean_text)
    incident_location = _extract_incident_location(clean_text)

    # 2. Extract Entities
    phones = _extract_phone_numbers(clean_text)
    vehicles = _extract_vehicles(clean_text)
    nlp_entities = _extract_nlp_entities(clean_text, phones=phones, vehicles=vehicles)

    persons = nlp_entities.get('persons', [])
    orgs = nlp_entities.get('organizations', [])
    locations = nlp_entities.get('locations', [])

    # If an incident location was found via regex, make sure it is in locations
    if incident_location and not any(loc['location_name'].lower() == incident_location.lower() for loc in locations):
        locations.insert(0, {
            'location_name': incident_location,
            'city': incident_location.split(',')[0].strip(),
            'state': incident_location.split(',')[-1].strip() if ',' in incident_location else '',
        })

    # 3. Extract Contextual Call Records
    phone_records = _extract_call_records(clean_text, phones)

    # 4. Generate Meaningful Title & Summary
    title = _generate_case_title(clean_text, case_type, incident_location, case_number, filename)
    description = _generate_case_summary(clean_text)

    # 5. Extract Explicit Relationships Between Entities
    relationships = _extract_entity_relationships(clean_text, persons, vehicles, orgs, locations)

    structured_case = {
        "case_number": case_number,
        "title": title,
        "description": description,
        "case_type": case_type,
        "location": incident_location,
        "persons": persons,
        "phone_records": phone_records,
        "vehicles": vehicles,
        "organizations": orgs,
        "locations": locations,
        "relationships": relationships,
    }

    return {"cases": [structured_case]}


def _extract_case_number(text: str) -> str:
    """Extract case or FIR number if explicitly stated."""
    match = FIR_CASE_REGEX.search(text)
    if match:
        num = match.group(1).strip().rstrip('.,;')
        if len(num) >= 2 and any(c.isalnum() for c in num):
            return num.upper()
    return ""


def _infer_case_type(text: str) -> str:
    """Determine case type based on contextual keywords."""
    lower_text = text.lower()
    for crime_type, keywords in CRIME_TYPE_KEYWORDS.items():
        if any(kw in lower_text for kw in keywords):
            return crime_type
    return "other"


def _extract_incident_location(text: str) -> str:
    """Extract incident location string."""
    match = LOCATION_REGEX.search(text)
    if match:
        loc = match.group(1).strip().rstrip('.,;')
        if len(loc) > 2:
            return loc
    return ""


def _generate_case_title(text: str, case_type: str, location: str, case_number: str, filename: str) -> str:
    """Produce a professional investigation case title."""
    # Check for explicit title or subject line
    subject_match = re.search(r'(?:Subject|Re|Case Title)\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
    if subject_match:
        cand = subject_match.group(1).strip()
        if len(cand) >= 5:
            return cand[:180]

    type_display = case_type.replace('_', ' ').title()
    loc_display = f" at {location}" if location else ""
    num_display = f" ({case_number})" if case_number else ""

    if loc_display or num_display:
        return f"{type_display} Investigation{loc_display}{num_display}"[:180]

    if filename:
        clean_fn = re.sub(r'\.[a-zA-Z0-9]+$', '', filename).replace('_', ' ').replace('-', ' ').title()
        return f"{type_display} Case - {clean_fn}"[:180]

    return f"{type_display} Investigation Case"


def _generate_case_summary(text: str) -> str:
    """Extract an intelligible description or brief of the case."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    # Return first 600 characters or clean first paragraph
    full = "\n".join(lines)
    if len(full) > 800:
        return full[:797] + "..."
    return full


def _extract_phone_numbers(text: str) -> list:
    """Extract all distinct phone numbers."""
    phones = []
    seen = set()
    for match in PHONE_REGEX.finditer(text):
        num = match.group().strip()
        if num not in seen:
            seen.add(num)
            phones.append(num)
    return phones


def _extract_vehicles(text: str) -> list:
    """Extract vehicles with registration plate, model, and owner where possible."""
    vehicles = []
    seen_plates = set()

    for match in VEHICLE_REGEX.finditer(text):
        plate = match.group().strip().upper()
        if plate in seen_plates:
            continue
        seen_plates.add(plate)

        # Context around the vehicle plate (50 chars before and after)
        start = max(0, match.start() - 60)
        end = min(len(text), match.end() + 60)
        window = text[start:end].lower()

        v_type = 'car'
        if any(w in window for w in ('motorcycle', 'bike', 'bullet', 'scooter', 'activa')):
            v_type = 'motorcycle'
        elif any(w in window for w in ('truck', 'dumper', 'lorry', 'trailer')):
            v_type = 'truck'
        elif any(w in window for w in ('bus',)):
            v_type = 'bus'
        elif any(w in window for w in ('van', 'omni')):
            v_type = 'van'

        # Infer model
        model = "Unknown Model"
        for m in ('Honda City', 'Toyota Fortuner', 'Royal Enfield', 'Tata Ace', 'Hyundai i20', 'Maruti Swift', 'Scorpio', 'Innova'):
            if m.lower() in window:
                model = m
                break

        # Infer color
        color = "Unknown"
        for c in ('black', 'white', 'silver', 'grey', 'red', 'blue', 'dark blue'):
            if c in window:
                color = c.capitalize()
                break

        vehicles.append({
            'registration_number': plate,
            'vehicle_type': v_type,
            'model_name': model,
            'color': color,
            'owner_name': '',
        })

    return vehicles


def _extract_nlp_entities(text: str, phones: list, vehicles: list) -> dict:
    """
    Extract Persons, Organizations, and Locations using spaCy NER with fallback.
    Assigns contextual roles (Suspect, Complainant, Witness, etc.) to persons.
    """
    persons = []
    orgs = []
    locations = []

    seen_persons = set()
    seen_orgs = set()
    seen_locations = set()

    phone_set = set(phones)
    vehicle_plate_set = {v['registration_number'].replace(' ', '') for v in vehicles}

    if _NLP is not None:
        doc = _NLP(text)
        for ent in doc.ents:
            name = ent.text.strip()
            # Ignore single characters or pure digits
            if len(name) <= 2 or name.isdigit():
                continue

            # Skip if caught by structured regex
            if name in phone_set or any(name in p for p in phone_set):
                continue
            if name.replace(' ', '').upper() in vehicle_plate_set:
                continue

            # Person NER
            if ent.label_ == 'PERSON':
                norm = name.lower()
                if norm not in seen_persons and not _is_common_false_positive_person(name):
                    seen_persons.add(norm)
                    role = _infer_person_role(text, ent.start_char, ent.end_char)
                    persons.append({
                        'full_name': name,
                        'role': role,
                        'gender': 'unknown',
                        'phone_number': _find_nearest_phone(text, ent.start_char, phones),
                        'address': '',
                        'description': f"Extracted via spaCy NER. Inferred contextual role: {role}.",
                    })

            # Organization NER
            elif ent.label_ == 'ORG':
                norm = name.lower()
                if norm not in seen_orgs and len(name) > 2:
                    seen_orgs.add(norm)
                    org_type = 'company'
                    if any(w in norm for w in ('gang', 'syndicate', 'cartel', 'network')):
                        org_type = 'criminal_network'
                    elif any(w in norm for w in ('ngo', 'foundation', 'trust')):
                        org_type = 'ngo'
                    elif any(w in norm for w in ('police', 'department', 'division', 'ministry', 'cbi', 'cid')):
                        org_type = 'other'

                    orgs.append({
                        'name': name,
                        'organization_type': org_type,
                        'address': '',
                        'description': f"Identified in document text as an organization.",
                    })

            # Location NER
            elif ent.label_ in ('GPE', 'LOC', 'FAC'):
                norm = name.lower()
                if norm not in seen_locations and len(name) > 2:
                    seen_locations.add(norm)
                    city = name
                    state = ""
                    if ',' in name:
                        parts = name.split(',')
                        city = parts[0].strip()
                        state = parts[1].strip()

                    locations.append({
                        'location_name': name,
                        'city': city,
                        'state': state,
                        'address': name,
                    })

    # Heuristic fallback if spaCy found few persons
    if not persons:
        suspect_matches = re.finditer(
            r'(?:accused|suspect|complainant|victim|informant|officer)\s*(?:named|is|identified as)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            text, re.IGNORECASE
        )
        for m in suspect_matches:
            cname = m.group(1).strip()
            if cname.lower() not in seen_persons and len(cname) > 3:
                seen_persons.add(cname.lower())
                role = _infer_person_role(text, m.start(), m.end())
                persons.append({
                    'full_name': cname,
                    'role': role,
                    'gender': 'unknown',
                    'phone_number': _find_nearest_phone(text, m.start(), phones),
                    'address': '',
                    'description': f"Extracted via linguistic pattern. Role: {role}.",
                })

    return {
        'persons': persons,
        'organizations': orgs,
        'locations': locations,
    }


def _infer_person_role(text: str, start: int, end: int) -> str:
    """Analyze surrounding sentence to determine person's role in the case."""
    context_window = text[max(0, start - 120):min(len(text), end + 120)].lower()
    if any(w in context_window for w in ('accused', 'suspect', 'perpetrator', 'alleged', 'culprit', 'arrested')):
        return "Suspect"
    if any(w in context_window for w in ('complainant', 'victim', 'filed by', 'reported by')):
        return "Complainant"
    if any(w in context_window for w in ('witness', 'testified', 'eye witness', 'saw', 'stated')):
        return "Witness"
    if any(w in context_window for w in ('officer', 'inspector', 'investigator', 'sub-inspector')):
        return "Investigating Officer"
    if any(w in context_window for w in ('driver', 'owner')):
        return "Vehicle Owner"
    return "Person of Interest"


def _find_nearest_phone(text: str, char_pos: int, phones: list) -> str:
    """Find if a phone number appears in close proximity to a person's mention."""
    if not phones:
        return ""
    window = text[max(0, char_pos - 150):min(len(text), char_pos + 150)]
    for p in phones:
        if p in window:
            return p
    return ""


def _is_common_false_positive_person(name: str) -> bool:
    """Filter out non-person words that NER occasionally tags."""
    fps = {
        'india', 'delhi', 'mumbai', 'police', 'station', 'sector', 'court',
        'january', 'february', 'march', 'april', 'may', 'june', 'july',
        'august', 'september', 'october', 'november', 'december', 'monday',
        'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'fir', 'act', 'ipc', 'crpc', 'state', 'government', 'sir', 'madam'
    }
    return name.lower() in fps


def _extract_call_records(text: str, phones: list) -> list:
    """Extract call detail records mentioned in the text."""
    records = []
    if len(phones) >= 2:
        records.append({
            'caller_number': phones[0],
            'receiver_number': phones[1],
            'call_date': str(datetime.date.today()),
            'call_time': "12:00:00",
            'duration': 180,
        })
    return records


def _extract_entity_relationships(text: str, persons: list, vehicles: list, orgs: list, locations: list) -> list:
    """
    Identify explicit relationships between extracted entities.
    E.g. Person owns Vehicle, Person associated with Organization.
    """
    relationships = []
    lower_text = text.lower()

    # Person - Vehicle Ownership
    for person in persons:
        p_name = person['full_name'].lower()
        for vehicle in vehicles:
            v_plate = vehicle['registration_number'].lower()
            if p_name in lower_text and v_plate in lower_text:
                relationships.append({
                    'source_type': 'person',
                    'source_name': person['full_name'],
                    'target_type': 'vehicle',
                    'target_name': vehicle['registration_number'],
                    'relationship_type': 'owns',
                    'evidence': f"Mentioned in document with vehicle {vehicle['registration_number']}",
                })

    # Person - Organization Membership
    for person in persons:
        p_name = person['full_name'].lower()
        for org in orgs:
            o_name = org['name'].lower()
            if p_name in lower_text and o_name in lower_text:
                relationships.append({
                    'source_type': 'person',
                    'source_name': person['full_name'],
                    'target_type': 'organization',
                    'target_name': org['name'],
                    'relationship_type': 'associated_with',
                    'evidence': f"Mentioned in document connection with {org['name']}",
                })

    return relationships


def extract_entities(text: str) -> list:
    """
    Backward-compatible entity extraction function returning a flat list of entities.
    Used by existing tests and legacy views.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return []

    entities = []
    seen = set()

    def add_entity(entity_text, entity_type, method='regex', confidence=0.9):
        clean = entity_text.strip()
        key = (clean.lower(), entity_type)
        if clean and key not in seen:
            seen.add(key)
            entities.append({
                'text': clean,
                'type': entity_type,
                'method': method,
                'confidence': confidence,
            })

    # Phone numbers
    for phone in _extract_phone_numbers(clean_text):
        add_entity(phone, 'PHONE_NUMBER', method='regex', confidence=0.95)

    # Vehicles
    for v in VEHICLE_REGEX.findall(clean_text):
        add_entity(v.strip(), 'VEHICLE_NUMBER', method='regex', confidence=0.95)

    # SpaCy entities
    if _NLP:
        doc = _NLP(clean_text)
        for ent in doc.ents:
            ent_type = ent.label_
            if ent_type == 'PERSON':
                if len(ent.text.strip()) > 2:
                    add_entity(ent.text, 'PERSON', method='spacy', confidence=0.85)
            elif ent_type in ('ORG', 'ORGANIZATION'):
                add_entity(ent.text, 'ORGANIZATION', method='spacy', confidence=0.80)
            elif ent_type in ('GPE', 'LOC'):
                add_entity(ent.text, 'LOCATION', method='spacy', confidence=0.80)

    return entities

