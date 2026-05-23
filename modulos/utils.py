import unicodedata
from typing import Iterable, List

DEPARTAMENTO_SINONIMOS = {
    "LIMA METROPOLITANA": "LIMA",
    "LIMA METROPOLITANO": "LIMA",
    "PROVINCIA DE LIMA": "LIMA",
    "REGION LIMA": "LIMA",
}

SPECIAL_CRIME_FILTERS = {
    "TODO": [],
    "TODOS": [],
    "SOLO_EXTORSION": ["EXTORSION"],
    "SOLO EXTORSION": ["EXTORSION"],
    "SOLO_SICARIATO": ["SICARIATO", "HOMICIDIO"],
    "SOLO SICARIATO": ["SICARIATO", "HOMICIDIO"],
    "AMBOS": ["EXTORSION", "SICARIATO", "HOMICIDIO"],
    "EXTORSION Y SICARIATO": ["EXTORSION", "SICARIATO", "HOMICIDIO"],
}


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    text = str(value).upper().strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalize_department_name(value: str) -> str:
    normalized = normalize_text(value)
    return DEPARTAMENTO_SINONIMOS.get(normalized, normalized)


def resolve_crime_filter(value: str) -> List[str]:
    if value is None:
        return []
    value_norm = normalize_text(value)
    if value_norm in SPECIAL_CRIME_FILTERS:
        return SPECIAL_CRIME_FILTERS[value_norm]
    if value_norm.endswith("S") and value_norm[:-1] in {"HOMICIDIO", "EXTORSION", "SICARIATO"}:
        value_norm = value_norm[:-1]
    return [value_norm] if value_norm else []


def normalize_crime_types(values: Iterable[str]) -> List[str]:
    return [normalize_text(v) for v in values if v is not None]
