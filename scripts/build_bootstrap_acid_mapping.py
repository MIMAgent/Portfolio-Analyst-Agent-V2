"""Build a draft ACID mapping file from current repo artifacts.

This script creates a bootstrap mapping that is intentionally heuristic.
It is meant to be reviewed and corrected by a human before being treated as
the long-term source of truth.
"""

from __future__ import annotations

import csv
from pathlib import Path


DEFAULT_SOURCE_CSV = Path("artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv")
DEFAULT_OUTPUT_CSV = Path("data/acid_mapping_bootstrap_v1.csv")


COUNTRY_NAMES = {
    "AE": "United Arab Emirates",
    "AT": "Austria",
    "AU": "Australia",
    "BE": "Belgium",
    "BR": "Brazil",
    "CA": "Canada",
    "CH": "Switzerland",
    "CL": "Chile",
    "CN": "China",
    "CO": "Colombia",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DK": "Denmark",
    "EG": "Egypt",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GR": "Greece",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IN": "India",
    "IT": "Italy",
    "JP": "Japan",
    "KR": "South Korea",
    "MX": "Mexico",
    "MY": "Malaysia",
    "NL": "Netherlands",
    "NO": "Norway",
    "NZ": "New Zealand",
    "PE": "Peru",
    "PH": "Philippines",
    "PL": "Poland",
    "PT": "Portugal",
    "QA": "Qatar",
    "SE": "Sweden",
    "SG": "Singapore",
    "TH": "Thailand",
    "TR": "Turkey",
    "TW": "Taiwan",
    "UK": "United Kingdom",
    "US": "United States",
    "ZA": "South Africa",
}

REGION_NAMES = {
    "EM": "Emerging Markets",
    "EU": "Europe",
    "JP": "Japan",
    "US": "United States",
    "AU": "Australia",
}

SECTOR_NAMES = {
    "CD": "Consumer Discretionary",
    "CS": "Consumer Staples",
    "EN": "Energy",
    "FN": "Financials",
    "HC": "Health Care",
    "ID": "Industrials",
    "IT": "Information Technology",
    "MT": "Materials",
    "RE": "Real Estate",
    "TL": "Communication Services",
    "UT": "Utilities",
}


FIELDNAMES = [
    "acid",
    "asset_class_name",
    "model_family",
    "family",
    "comparison_group",
    "relative_value_group",
    "interpretation_type",
    "investable_flag",
    "subtype",
    "market_scope",
    "region",
    "country",
    "sector",
    "style",
    "currency_exposure_type",
    "maturity_bucket",
    "curve_aware",
    "parent_family",
    "index_provider",
    "benchmark_role",
    "notes",
]


def main() -> None:
    rows = _load_unique_acids(DEFAULT_SOURCE_CSV)
    mapped_rows = [_build_mapping_row(acid_type=acid_type, acid=acid) for acid_type, acid in rows]

    DEFAULT_OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(mapped_rows)

    print(f"acid_mapping_count={len(mapped_rows)}")
    print(f"acid_mapping_csv={DEFAULT_OUTPUT_CSV}")


def _load_unique_acids(source_csv: Path) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    with source_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            acid = row.get("acid", "").strip()
            acid_type = row.get("acid_type", "").strip()
            if acid and acid_type:
                seen.add((acid_type, acid))
    return sorted(seen, key=lambda item: (item[0], item[1]))


def _build_mapping_row(*, acid_type: str, acid: str) -> dict[str, str]:
    if acid_type == "acid_country":
        return _country_row(acid)
    if acid_type == "acid_region_sector":
        return _region_sector_row(acid)
    if acid_type == "acid_bond":
        return _bond_row(acid)
    return _fallback_row(acid=acid, notes=f"Unrecognized acid_type: {acid_type}")


def _country_row(acid: str) -> dict[str, str]:
    if acid == "US EQ":
        return _row(
            acid=acid,
            asset_class_name="United States Equity",
            model_family="equity",
            family="US Equity",
            comparison_group="us_equity_broad",
            relative_value_group="us_equity_broad",
            interpretation_type="broad_market_beta",
            investable_flag="true",
            market_scope="United States",
            region="United States",
            country="United States",
            curve_aware="false",
            parent_family="",
            notes="Bootstrap broad US equity parent exposure.",
        )

    if acid in {"US LRG EQ", "US MID EQ", "US SML EQ"}:
        size_name = acid.replace("US ", "").replace(" EQ", "")
        return _row(
            acid=acid,
            asset_class_name=f"United States {size_name.title()} Equity",
            model_family="equity",
            family="US Equity Size",
            comparison_group="us_equity_size_buckets",
            relative_value_group="us_equity_size_buckets",
            interpretation_type="broad_market_beta",
            investable_flag="true",
            market_scope="United States",
            region="United States",
            country="United States",
            style=_style_from_acid(acid),
            curve_aware="false",
            parent_family="US EQ",
            notes="Bootstrap size-bucket parent exposure under broad US equity.",
        )

    if acid in {"US LRG G EQ", "US LRG V EQ", "US MID G EQ", "US MID V EQ", "US SML G EQ", "US SML V EQ"}:
        size_bucket = "US LRG EQ" if "LRG" in acid else "US MID EQ" if "MID" in acid else "US SML EQ"
        style = "Growth" if " G " in f" {acid} " else "Value"
        return _row(
            acid=acid,
            asset_class_name=f"United States {size_bucket.replace('US ', '').replace(' EQ', '').title()} {style} Equity",
            model_family="equity",
            family="US Equity Style",
            comparison_group="us_equity_styles",
            relative_value_group=size_bucket.lower().replace(" ", "_"),
            interpretation_type="style_relative_value",
            investable_flag="true",
            market_scope="United States",
            region="United States",
            country="United States",
            style=style,
            curve_aware="false",
            parent_family=size_bucket,
            notes="Bootstrap style child exposure under US size bucket.",
        )

    if acid == "EM EQ":
        return _row(
            acid=acid,
            asset_class_name="Emerging Markets Equity",
            model_family="equity",
            family="Emerging Markets Equity",
            comparison_group="global_country_equities",
            relative_value_group="em_country_equities",
            interpretation_type="region_relative_value",
            investable_flag="true",
            market_scope="Emerging Markets",
            region="Emerging Markets",
            country="",
            curve_aware="false",
            parent_family="",
            notes="Bootstrap regional emerging-markets parent exposure.",
        )

    if acid == "ARAB EQ":
        return _row(
            acid=acid,
            asset_class_name="Arab Markets Equity",
            model_family="equity",
            family="Emerging Markets Equity",
            comparison_group="global_country_equities",
            relative_value_group="em_country_equities",
            interpretation_type="region_relative_value",
            investable_flag="true",
            market_scope="Arab Markets",
            region="Emerging Markets",
            country="",
            curve_aware="false",
            parent_family="EM EQ",
            notes="Bootstrap regional country-basket exposure.",
        )

    country_code = acid.split(" ", 1)[0]
    country_name = COUNTRY_NAMES.get(country_code, country_code)
    region = _region_from_country_code(country_code)
    return _row(
        acid=acid,
        asset_class_name=f"{country_name} Equity",
        model_family="equity",
        family="Country Equity",
        comparison_group="global_country_equities",
        relative_value_group=f"{region.lower().replace(' ', '_')}_country_equities" if region else "global_country_equities",
        interpretation_type="region_relative_value",
        investable_flag="true",
        market_scope=country_name,
        region=region,
        country=country_name,
        curve_aware="false",
        parent_family="EM EQ" if region == "Emerging Markets" else "",
        notes="Bootstrap country equity exposure generated from current artifact ACIDs.",
    )


def _region_sector_row(acid: str) -> dict[str, str]:
    prefix, sector_code, *_ = acid.split(" ")
    region_name = REGION_NAMES.get(prefix, prefix)
    sector_name = SECTOR_NAMES.get(sector_code, sector_code)
    parent = f"{prefix} EQ"
    return _row(
        acid=acid,
        asset_class_name=f"{region_name} {sector_name} Equity",
        model_family="equity",
        family="Equity Sector",
        comparison_group=f"{prefix.lower()}_equity_sectors",
        relative_value_group=f"{prefix.lower()}_equity_sectors",
        interpretation_type="sector_relative_value",
        investable_flag="true",
        market_scope=region_name,
        region=region_name,
        country="United States" if prefix == "US" else "Japan" if prefix == "JP" else "",
        sector=sector_name,
        curve_aware="false",
        parent_family=parent,
        notes="Bootstrap regional/country sector exposure generated from current artifact ACIDs.",
    )


def _bond_row(acid: str) -> dict[str, str]:
    if acid == "USD Cash":
        return _row(
            acid=acid,
            asset_class_name="USD Cash",
            model_family="fixed_income",
            family="Cash",
            comparison_group="cash_and_short_duration",
            relative_value_group="cash_and_short_duration",
            interpretation_type="cash_proxy",
            investable_flag="false",
            subtype="cash",
            currency_exposure_type="USD",
            curve_aware="false",
            parent_family="",
            notes="Bootstrap cash row; excluded from better-expression logic by default.",
        )

    if acid == "Alts":
        return _row(
            acid=acid,
            asset_class_name="Alternatives",
            model_family="multi_asset",
            family="Alternatives",
            comparison_group="alternatives",
            relative_value_group="alternatives",
            interpretation_type="broad_market_beta",
            investable_flag="true",
            subtype="alternatives",
            curve_aware="false",
            notes="Bootstrap alternatives sleeve placeholder.",
        )

    if " Muni:" in acid or acid.startswith("US Muni"):
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family="Municipal Bonds",
            comparison_group="us_muni_curve",
            relative_value_group="us_muni_curve",
            interpretation_type="curve_segment_relative_value",
            investable_flag="true",
            subtype="municipal",
            market_scope="United States",
            region="United States",
            currency_exposure_type="USD",
            maturity_bucket=_maturity_bucket_from_bond_acid(acid),
            curve_aware="true",
            parent_family="US Muni",
            notes="Bootstrap municipal curve exposure.",
        )

    if acid.startswith("EM HC T") or acid.startswith("EM LC T"):
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family="Emerging Market Sovereign",
            comparison_group="em_sovereign_bonds",
            relative_value_group="em_sovereign_bonds",
            interpretation_type="region_relative_value",
            investable_flag="true",
            subtype="sovereign",
            market_scope="Emerging Markets",
            region="Emerging Markets",
            currency_exposure_type="hard_currency" if "HC" in acid else "local_currency",
            curve_aware="false",
            notes="Bootstrap emerging sovereign bond exposure.",
        )

    if " T:" in acid or acid.endswith(" T") or acid.startswith("US T") or acid.startswith("AU T") or acid.startswith("EU T") or acid.startswith("JP T") or acid.startswith("UK T") or acid.startswith("CA T"):
        prefix = acid.split(" ", 1)[0]
        market_scope = _bond_market_scope(prefix)
        family = "Treasury"
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family=family,
            comparison_group=f"{prefix.lower()}_treasury_curve",
            relative_value_group=f"{prefix.lower()}_treasury_curve",
            interpretation_type="curve_segment_relative_value",
            investable_flag="true",
            subtype="government",
            market_scope=market_scope,
            region=market_scope,
            currency_exposure_type=_currency_from_prefix(prefix),
            maturity_bucket=_maturity_bucket_from_bond_acid(acid),
            curve_aware="true",
            parent_family=prefix + " T" if ":" in acid else "",
            notes="Bootstrap treasury curve exposure.",
        )

    if " Corp" in acid:
        prefix = acid.split(" ", 1)[0]
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family="Corporate Credit",
            comparison_group=f"{prefix.lower()}_corporate_credit",
            relative_value_group=f"{prefix.lower()}_corporate_credit",
            interpretation_type="spread_product_relative_value",
            investable_flag="true",
            subtype="corporate",
            market_scope=_bond_market_scope(prefix),
            region=_bond_market_scope(prefix),
            currency_exposure_type=_currency_from_prefix(prefix),
            maturity_bucket=_maturity_bucket_from_bond_acid(acid),
            curve_aware="true" if ":" in acid else "false",
            parent_family=prefix + " Corp" if ":" in acid else "",
            notes="Bootstrap corporate credit exposure.",
        )

    if " Agg" in acid:
        prefix = acid.split(" ", 1)[0]
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family="Aggregate Bonds",
            comparison_group="global_aggregate_bonds",
            relative_value_group="global_aggregate_bonds",
            interpretation_type="benchmark_anchor",
            investable_flag="true",
            subtype="aggregate",
            market_scope=_bond_market_scope(prefix),
            region=_bond_market_scope(prefix),
            currency_exposure_type=_currency_from_prefix(prefix),
            curve_aware="false",
            notes="Bootstrap broad aggregate bond exposure.",
        )

    if " IL:" in acid:
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family="Inflation-Linked Bonds",
            comparison_group="inflation_linked_curve",
            relative_value_group="inflation_linked_curve",
            interpretation_type="inflation_sensitive_expression",
            investable_flag="true",
            subtype="inflation_linked",
            market_scope="United States",
            region="United States",
            currency_exposure_type="USD",
            maturity_bucket=_maturity_bucket_from_bond_acid(acid),
            curve_aware="true",
            parent_family="US IL",
            notes="Bootstrap inflation-linked curve exposure.",
        )

    if "GovRltd" in acid or "Gov:" in acid:
        prefix = acid.split(" ", 1)[0]
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family="Government Related",
            comparison_group=f"{prefix.lower()}_government_related",
            relative_value_group=f"{prefix.lower()}_government_related",
            interpretation_type="benchmark_anchor",
            investable_flag="true",
            subtype="government_related",
            market_scope=_bond_market_scope(prefix),
            region=_bond_market_scope(prefix),
            currency_exposure_type=_currency_from_prefix(prefix),
            maturity_bucket=_maturity_bucket_from_bond_acid(acid),
            curve_aware="true" if ":" in acid else "false",
            notes="Bootstrap government-related bond exposure.",
        )

    if "Secu" in acid:
        prefix = acid.split(" ", 1)[0]
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family="Securitized Credit",
            comparison_group=f"{prefix.lower()}_securitized_credit",
            relative_value_group=f"{prefix.lower()}_securitized_credit",
            interpretation_type="spread_product_relative_value",
            investable_flag="true",
            subtype="securitized",
            market_scope=_bond_market_scope(prefix),
            region=_bond_market_scope(prefix),
            currency_exposure_type=_currency_from_prefix(prefix),
            curve_aware="false",
            notes="Bootstrap securitized credit exposure.",
        )

    if acid == "Gbl Corp: HY" or acid == "PanEU Corp: HY":
        return _row(
            acid=acid,
            asset_class_name=acid,
            model_family="fixed_income",
            family="High Yield Credit",
            comparison_group="high_yield_credit",
            relative_value_group="high_yield_credit",
            interpretation_type="spread_product_relative_value",
            investable_flag="true",
            subtype="high_yield",
            curve_aware="false",
            notes="Bootstrap high-yield credit exposure.",
        )

    return _row(
        acid=acid,
        asset_class_name=acid,
        model_family="fixed_income",
        family="Fixed Income",
        comparison_group="fixed_income_misc",
        relative_value_group="fixed_income_misc",
        interpretation_type="benchmark_anchor",
        investable_flag="true",
        curve_aware="false",
        notes="Bootstrap fallback fixed-income mapping; review manually.",
    )


def _fallback_row(*, acid: str, notes: str) -> dict[str, str]:
    return _row(
        acid=acid,
        asset_class_name=acid,
        model_family="unknown",
        family="Unknown",
        comparison_group="unmapped",
        relative_value_group="unmapped",
        interpretation_type="broad_market_beta",
        investable_flag="false",
        curve_aware="false",
        notes=notes,
    )


def _row(**values: str) -> dict[str, str]:
    row = {field: "" for field in FIELDNAMES}
    row.update(values)
    return row


def _region_from_country_code(code: str) -> str:
    if code in {"BR", "CL", "CN", "CO", "CZ", "EG", "HU", "ID", "IN", "KR", "MX", "MY", "PE", "PH", "PL", "QA", "TH", "TR", "TW", "ZA", "AE"}:
        return "Emerging Markets"
    if code in {"AT", "BE", "CH", "DE", "DK", "ES", "FI", "FR", "GR", "IE", "IT", "NL", "NO", "PT", "SE", "UK"}:
        return "Developed Europe"
    if code in {"AU", "NZ", "JP", "HK", "SG", "IL"}:
        return "Asia Pacific"
    if code in {"CA", "US"}:
        return "North America"
    return ""


def _style_from_acid(acid: str) -> str:
    if " G EQ" in acid:
        return "Growth"
    if " V EQ" in acid:
        return "Value"
    return ""


def _bond_market_scope(prefix: str) -> str:
    return {
        "AU": "Australia",
        "CA": "Canada",
        "EU": "Europe",
        "JP": "Japan",
        "UK": "United Kingdom",
        "US": "United States",
        "EM": "Emerging Markets",
        "Gbl": "Global",
        "PanEU": "Pan-Europe",
    }.get(prefix, prefix)


def _currency_from_prefix(prefix: str) -> str:
    return {
        "AU": "AUD",
        "CA": "CAD",
        "EU": "EUR",
        "JP": "JPY",
        "UK": "GBP",
        "US": "USD",
        "EM": "mixed",
        "Gbl": "mixed",
        "PanEU": "EUR",
    }.get(prefix, "")


def _maturity_bucket_from_bond_acid(acid: str) -> str:
    if ":" not in acid:
        return ""
    return acid.split(":", 1)[1].strip()


if __name__ == "__main__":
    main()
