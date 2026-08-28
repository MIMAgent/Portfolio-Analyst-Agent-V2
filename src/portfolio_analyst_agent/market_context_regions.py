"""Shared vocabulary for reading an ACID's region and category.

An ACID is positional: ``<REGION> [<CATEGORY CODE>] EQ`` — ``US ID EQ`` is US
industrials, ``EU ID EQ`` is European industrials, and a bare ``ID EQ`` is
Indonesia. The exposure *label* is region-agnostic ("Industrials" for both the
US and the European sector), so anything that scopes, queries, or filters
market context by label alone silently conflates regions. This module is the
single place that turns an ACID into the region and topic words those callers
need, so the bridge (query building, cache scope, source eligibility) and the
search relevance gate cannot drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AcidParts:
    """The positional decomposition of an ACID."""

    raw: str
    region_code: str
    category_code: str

    @property
    def is_country_or_region(self) -> bool:
        return not self.category_code


# Query-facing adjective, e.g. "European industrials sector".
_REGION_ADJECTIVE = {
    "US": "US",
    "EU": "European",
    "UK": "UK",
    "JP": "Japanese",
    "EM": "emerging market",
    "ARAB": "Middle East",
    "CN": "China",
    "HK": "Hong Kong",
    "TW": "Taiwan",
    "KR": "Korea",
    "IN": "India",
    "ID": "Indonesia",
    "TH": "Thailand",
    "MY": "Malaysia",
    "SG": "Singapore",
    "PH": "Philippines",
    "AU": "Australia",
    "NZ": "New Zealand",
    "CA": "Canada",
    "MX": "Mexico",
    "BR": "Brazil",
    "CL": "Chile",
    "CO": "Colombia",
    "PE": "Peru",
    "ZA": "South Africa",
    "EG": "Egypt",
    "IL": "Israel",
    "AE": "UAE",
    "QA": "Qatar",
    "TR": "Turkey",
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "ES": "Spain",
    "PT": "Portugal",
    "GR": "Greece",
    "NL": "Netherlands",
    "BE": "Belgium",
    "AT": "Austria",
    "CH": "Switzerland",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "FI": "Finland",
    "IE": "Ireland",
    "PL": "Poland",
    "HU": "Hungary",
    "CZ": "Czech Republic",
}

# Lowercase words that mark a passage of text as being about this region.
_REGION_TOKENS = {
    "US": {"us", "u.s", "usa", "united", "states", "american", "america", "domestic"},
    "EU": {"europe", "european", "euro", "eurozone", "emu", "stoxx"},
    "UK": {"uk", "britain", "british", "england", "gilt", "ftse"},
    "JP": {"japan", "japanese", "yen", "topix", "nikkei", "boj"},
    "EM": {"emerging", "developing", "frontier"},
    "ARAB": {"gulf", "gcc", "middle", "east", "arab"},
}
for _code, _name in _REGION_ADJECTIVE.items():
    _REGION_TOKENS.setdefault(_code, {_code.lower(), *_name.lower().split()})

# Topic words a passage must touch to count as being about this category.
_CATEGORY_TOKENS = {
    "IT": {"technology", "tech", "information", "software", "hardware", "semiconductor", "semiconductors", "ai", "cloud"},
    "ID": {"industrial", "industrials", "manufacturing", "orders", "pmi", "capex", "cyclical", "aerospace", "defense", "machinery", "transport"},
    "FN": {"financial", "financials", "bank", "banks", "banking", "insurance", "lending", "credit", "rates", "spreads"},
    "CD": {"consumer", "discretionary", "retail", "retailer", "autos", "auto", "leisure", "housing", "spending"},
    "CS": {"consumer", "staples", "food", "beverage", "household", "grocery", "tobacco"},
    "EN": {"energy", "oil", "gas", "crude", "refining", "drilling", "opec"},
    "HC": {"health", "healthcare", "pharma", "pharmaceutical", "biotech", "medical", "device", "devices"},
    "MT": {"materials", "mining", "chemicals", "chemical", "metals", "steel", "copper", "commodity"},
    "RE": {"real", "estate", "reit", "reits", "property", "rents", "occupancy"},
    "TL": {"communication", "communications", "telecom", "media", "advertising", "streaming", "internet"},
    "UT": {"utilities", "utility", "power", "electricity", "grid", "regulated"},
    "LRG": {"large", "cap", "megacap", "mega", "broad"},
    "MID": {"mid", "cap", "midcap"},
    "SML": {"small", "cap", "smallcap", "smid", "russell"},
    "G": {"growth", "momentum", "multiple", "duration"},
    "V": {"value", "cheap", "cyclical", "dividend"},
}

# Natural-language subject for a category code, used to phrase queries.
_CATEGORY_SUBJECT = {
    "IT": "information technology sector",
    "ID": "industrials sector",
    "FN": "financials sector",
    "CD": "consumer discretionary sector",
    "CS": "consumer staples sector",
    "EN": "energy sector",
    "HC": "health care sector",
    "MT": "materials sector",
    "RE": "real estate sector",
    "TL": "communication services sector",
    "UT": "utilities sector",
    "LRG": "large-cap equities",
    "MID": "mid-cap equities",
    "SML": "small-cap equities",
    "LRG G": "large-cap growth equities",
    "LRG V": "large-cap value equities",
    "MID G": "mid-cap growth equities",
    "MID V": "mid-cap value equities",
    "SML G": "small-cap growth equities",
    "SML V": "small-cap value equities",
}


def parse_acid(acid: str) -> AcidParts:
    """Split an ACID positionally into region and category code.

    ``US ID EQ`` -> region ``US``, category ``ID``. ``ID EQ`` -> region ``ID``,
    no category (Indonesia, the country). ``US SML V EQ`` -> category ``SML V``.
    """

    raw = str(acid or "").strip()
    tokens = raw.split()
    if not tokens:
        return AcidParts(raw="", region_code="", category_code="")
    region = tokens[0].upper()
    category = " ".join(tokens[1:-1]).upper() if len(tokens) >= 3 else ""
    return AcidParts(raw=raw, region_code=region, category_code=category)


def region_code(acid: str) -> str:
    return parse_acid(acid).region_code


def region_adjective(code: str) -> str:
    """Query-facing adjective for a region code; falls back to the code itself."""

    code = str(code or "").strip().upper()
    return _REGION_ADJECTIVE.get(code, code)


def region_tokens(code: str) -> set[str]:
    code = str(code or "").strip().upper()
    if not code:
        return set()
    return set(_REGION_TOKENS.get(code, {code.lower()}))


def category_tokens(code: str) -> set[str]:
    """Topic words for a category code, unioned across a compound code."""

    code = str(code or "").strip().upper()
    if not code:
        return set()
    tokens: set[str] = set()
    for part in code.split():
        tokens.update(_CATEGORY_TOKENS.get(part, set()))
    return tokens


def category_subject(code: str) -> str:
    """Natural-language subject for a category code, or '' when unknown."""

    code = str(code or "").strip().upper()
    if not code:
        return ""
    return _CATEGORY_SUBJECT.get(code, "")


def known_region_codes() -> set[str]:
    return set(_REGION_ADJECTIVE)


def conflicting_region_codes(code: str) -> set[str]:
    """Region codes whose presence in a passage contradicts ``code``.

    Only the broad blocs are treated as contradictory. A US document naming
    "Japan" in passing should not be rejected outright, but a passage that is
    about Japan and never mentions the US must not be filed under a US exposure.
    """

    code = str(code or "").strip().upper()
    blocs = {"US", "EU", "UK", "JP", "EM", "CN"}
    if code not in blocs:
        return set()
    return blocs - {code}


__all__ = [
    "AcidParts",
    "category_subject",
    "category_tokens",
    "conflicting_region_codes",
    "known_region_codes",
    "parse_acid",
    "region_adjective",
    "region_code",
    "region_tokens",
]
