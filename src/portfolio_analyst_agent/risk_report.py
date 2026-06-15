"""Parse US equity risk report workbooks into agent-ready context."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from .parse_utils import safe_float
from .workbook_xml import XlsxWorkbook

INDUSTRY_TO_SECTOR = {
    "Aerospace & Defense": "Industrials",
    "Air Freight & Logistics": "Industrials",
    "Airlines": "Industrials",
    "Auto Components": "Consumer Discretionary",
    "Automobiles": "Consumer Discretionary",
    "Banks": "Financials",
    "Beverages": "Consumer Staples",
    "Biotechnology": "Health Care",
    "Building Products": "Industrials",
    "Capital Markets": "Financials",
    "Chemicals": "Materials",
    "Commercial Services & Supplies": "Industrials",
    "Communications Equipment": "Information Technology",
    "Construction & Engineering": "Industrials",
    "Construction Materials": "Materials",
    "Consumer Finance": "Financials",
    "Containers & Packaging": "Materials",
    "Distributors": "Consumer Discretionary",
    "Diversified Consumer Services": "Consumer Discretionary",
    "Diversified Financial Services": "Financials",
    "Diversified Telecommunication Services": "Communication Services",
    "Electric Utilities": "Utilities",
    "Electrical Equipment": "Industrials",
    "Electronic Equipment, Instruments & Components": "Information Technology",
    "Energy Equipment & Services": "Energy",
    "Equity Real Estate Investment Trusts (REITs)": "Real Estate",
    "Food & Staples Retailing": "Consumer Staples",
    "Food Products": "Consumer Staples",
    "Gas Utilities": "Utilities",
    "Health Care Equipment & Supplies": "Health Care",
    "Health Care Providers & Services": "Health Care",
    "Health Care Technology": "Health Care",
    "Hotels, Restaurants & Leisure": "Consumer Discretionary",
    "Household Durables": "Consumer Discretionary",
    "Household Products": "Consumer Staples",
    "Independent Power and Renewable Electricity Producers": "Utilities",
    "Industrial Conglomerates": "Industrials",
    "Insurance": "Financials",
    "Internet Software & Services": "Communication Services",
    "IT Services": "Information Technology",
    "Leisure Products": "Consumer Discretionary",
    "Life Sciences Tools & Services": "Health Care",
    "Machinery": "Industrials",
    "Marine": "Industrials",
    "Media": "Communication Services",
    "Metals & Mining": "Materials",
    "Mortgage Real Estate Investment Trusts (REITs)": "Financials",
    "Multiline Retail": "Consumer Discretionary",
    "Multi-Utilities": "Utilities",
    "Oil, Gas & Consumable Fuels": "Energy",
    "Paper & Forest Products": "Materials",
    "Personal Products": "Consumer Staples",
    "Pharmaceuticals": "Health Care",
    "Professional Services": "Industrials",
    "Real Estate Management & Development": "Real Estate",
    "Road & Rail": "Industrials",
    "Semiconductors & Semiconductor Equipment": "Information Technology",
    "Software": "Information Technology",
    "Specialty Retail": "Consumer Discretionary",
    "Technology Hardware, Storage & Peripherals": "Information Technology",
    "Textiles, Apparel & Luxury Goods": "Consumer Discretionary",
    "Tobacco": "Consumer Staples",
    "Trading Companies & Distributors": "Industrials",
    "Water Utilities": "Utilities",
    "Wireless Telecommunication Services": "Communication Services",
}


@dataclass(frozen=True)
class RiskReportParseResult:
    workbook_path: Path
    settings: dict[str, str]
    portfolio_details: list[dict[str, Any]]
    risk_details: list[dict[str, Any]]
    factor_risk_stddev: list[dict[str, Any]]
    active_factor_risk_pct_var: list[dict[str, Any]]
    return_details: list[dict[str, Any]]


def parse_risk_report_workbook(workbook_path: str | Path) -> RiskReportParseResult:
    workbook_path = Path(workbook_path)
    workbook = XlsxWorkbook(workbook_path)
    return RiskReportParseResult(
        workbook_path=workbook_path,
        settings=_parse_settings(workbook),
        portfolio_details=_parse_table_sheet(workbook, "PortfolioDetails"),
        risk_details=_parse_table_sheet(workbook, "Risk Details"),
        factor_risk_stddev=_parse_table_sheet(workbook, "Factor Risk (Std Dev)"),
        active_factor_risk_pct_var=_parse_table_sheet(workbook, "Active Factor Risk (% of Var)"),
        return_details=_parse_table_sheet(workbook, "Return Details"),
    )


def build_risk_context(
    workbook_path: str | Path,
    *,
    review_date: str | date,
    material_positions: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    parsed = parse_risk_report_workbook(workbook_path)
    review_day = review_date if isinstance(review_date, date) else date.fromisoformat(review_date)

    latest_risk_row = _latest_row_on_or_before(parsed.risk_details, review_day)
    if latest_risk_row is None:
        return {
            "available": False,
            "source_file": parsed.workbook_path.name,
            "requested_review_date": review_day.isoformat(),
            "message": "No usable risk row exists on or before the requested review date.",
        }

    prior_month_end = _previous_month_end(review_day)
    prior_risk_row = _latest_row_on_or_before(parsed.risk_details, prior_month_end)
    latest_date = latest_risk_row["date"]
    portfolio_row = _row_for_date(parsed.portfolio_details, latest_date)

    top_style = _top_factor_drivers(
        rows=parsed.active_factor_risk_pct_var,
        target_date=latest_date,
        prefix="Style Factors - ",
        top_n=5,
    )
    top_industry = _top_factor_drivers(
        rows=parsed.active_factor_risk_pct_var,
        target_date=latest_date,
        prefix="Industry Factors - ",
        top_n=6,
    )
    return_mtd = _compound_returns(parsed.return_details, month=review_day.month, year=review_day.year, end_date=latest_date)
    holdings_contributors = _match_holdings_to_risk_drivers(material_positions or [], top_industry)
    specific_watchlist = _specific_risk_watchlist(material_positions or [])

    summary = {
        "review_date_requested": review_day.isoformat(),
        "risk_date_used": latest_date.isoformat(),
        "prior_month_end_used": prior_risk_row["date"].isoformat() if prior_risk_row else "",
        "predicted_beta": _round_or_none(latest_risk_row.get("Predicted Beta"), 4),
        "active_predicted_beta": _round_or_none(latest_risk_row.get("Active Predicted Beta"), 4),
        "total_predicted_risk_pct": _pct(latest_risk_row.get("Total Predicted Risk")),
        "active_predicted_risk_pct": _pct(latest_risk_row.get("Active Predicted Risk")),
        "active_share_pct": _pct(latest_risk_row.get("Active Share")),
        "factor_risk_pct": _pct(latest_risk_row.get("Factor Risk")),
        "specific_risk_pct": _pct(latest_risk_row.get("Specific Risk")),
        "active_factor_risk_pct": _pct(latest_risk_row.get("Active Factor Risk")),
        "active_specific_risk_pct": _pct(latest_risk_row.get("Active Specific Risk")),
        "active_style_factor_risk_pct": _pct(latest_risk_row.get("Active Style Factor Risk")),
        "active_industry_factor_risk_pct": _pct(latest_risk_row.get("Active Industry Factor Risk")),
        "active_market_factor_risk_pct": _pct(latest_risk_row.get("Active Market Factor Risk")),
        "change_vs_prior_month_end": _risk_change_block(latest_risk_row, prior_risk_row),
    }

    coverage = {}
    if portfolio_row:
        coverage = {
            "asset_count": _int_or_none(portfolio_row.get("Total # of Assets")),
            "common_asset_count": _int_or_none(portfolio_row.get("# of Common Assets")),
            "common_asset_weight_pct": _pct(portfolio_row.get("% Weight of Common Assets")),
            "cash_weight_pct": _pct(portfolio_row.get("Cash Weight")),
        }

    return {
        "available": True,
        "source_file": parsed.workbook_path.name,
        "portfolio_code": parsed.settings.get("Portfolio", ""),
        "benchmark": parsed.settings.get("Benchmark", ""),
        "date_range": parsed.settings.get("Date Range", ""),
        "report_generated_with": parsed.settings.get("Report Generated Using", ""),
        "summary": summary,
        "portfolio_coverage": coverage,
        "top_style_risk_drivers": top_style,
        "top_industry_risk_drivers": top_industry,
        "return_attribution_mtd": return_mtd,
        "likely_holdings_contributors": holdings_contributors,
        "specific_risk_watchlist": specific_watchlist,
        "narrative_observations": _narrative_observations(
            summary=summary,
            top_style=top_style,
            top_industry=top_industry,
            return_mtd=return_mtd,
            holdings_contributors=holdings_contributors,
            specific_watchlist=specific_watchlist,
        ),
    }


def _parse_settings(workbook: XlsxWorkbook) -> dict[str, str]:
    worksheet = workbook.worksheet("Report Settings")
    settings: dict[str, str] = {}
    for row_number in sorted(worksheet.rows):
        value = worksheet.get_cell(row_number, 1).strip()
        if not value or ":" not in value:
            continue
        key, raw_value = value.split(":", 1)
        settings[key.strip()] = raw_value.strip()
    return settings


def _parse_table_sheet(workbook: XlsxWorkbook, sheet_name: str) -> list[dict[str, Any]]:
    worksheet = workbook.worksheet(sheet_name)
    headers = {column_number: value.replace("\n", " ").strip() for column_number, value in worksheet.nonempty_cells(1)}
    rows: list[dict[str, Any]] = []
    for row_number in sorted(worksheet.rows):
        if row_number == 1:
            continue
        row_date = worksheet.get_cell(row_number, 3).strip()
        if not row_date:
            continue
        parsed: dict[str, Any] = {"date": date.fromisoformat(row_date)}
        for column_number, header in headers.items():
            raw_value = worksheet.get_cell(row_number, column_number).strip()
            if column_number <= 3:
                parsed[header] = raw_value
                continue
            parsed[header] = safe_float(raw_value, context=f"{sheet_name}!r{row_number}c{column_number}")
        rows.append(parsed)
    return rows


def _latest_row_on_or_before(rows: Sequence[Mapping[str, Any]], target_date: date) -> Mapping[str, Any] | None:
    eligible = [row for row in rows if row.get("date") and row["date"] <= target_date]
    if not eligible:
        return None
    return max(eligible, key=lambda row: row["date"])


def _row_for_date(rows: Sequence[Mapping[str, Any]], target_date: date) -> Mapping[str, Any] | None:
    for row in rows:
        if row.get("date") == target_date:
            return row
    return None


def _previous_month_end(current_date: date) -> date:
    if current_date.month == 1:
        return date(current_date.year - 1, 12, 31)
    prior_month = current_date.month - 1
    return date(current_date.year, prior_month, calendar.monthrange(current_date.year, prior_month)[1])


def _top_factor_drivers(
    *,
    rows: Sequence[Mapping[str, Any]],
    target_date: date,
    prefix: str,
    top_n: int,
) -> list[dict[str, Any]]:
    row = _row_for_date(rows, target_date)
    if row is None:
        return []
    drivers: list[dict[str, Any]] = []
    for header, value in row.items():
        if not isinstance(header, str) or not header.startswith(prefix):
            continue
        if header.endswith("Covariance"):
            continue
        if value is None:
            continue
        drivers.append(
            {
                "label": header.removeprefix(prefix).strip(),
                "share_of_variance_pct": _pct(value),
            }
        )
    drivers.sort(key=lambda item: abs(item["share_of_variance_pct"] or 0.0), reverse=True)
    return drivers[:top_n]


def _compound_returns(
    rows: Sequence[Mapping[str, Any]],
    *,
    month: int,
    year: int,
    end_date: date,
) -> dict[str, Any]:
    period_rows = [
        row
        for row in rows
        if row["date"].year == year and row["date"].month == month and row["date"] <= end_date
    ]
    if not period_rows:
        return {}
    fields = [
        "Active Period Return",
        "Active Period Factor Return",
        "Active Period Specific Return",
        "Period Overweight Return",
        "Period Underweight Return",
        "Active Style Factor Returns",
        "Active Industry Factor Returns",
        "Active Market Factor Returns",
    ]
    compounded = {
        _canonical_return_name(field): _pct(_compound_field(period_rows, field))
        for field in fields
    }
    compounded["window_start"] = period_rows[0]["date"].isoformat()
    compounded["window_end"] = period_rows[-1]["date"].isoformat()
    return compounded


def _compound_field(rows: Sequence[Mapping[str, Any]], field: str) -> float | None:
    values = [row.get(field) for row in rows if row.get(field) is not None]
    if not values:
        return None
    result = 1.0
    for value in values:
        result *= 1.0 + float(value)
    return result - 1.0


def _match_holdings_to_risk_drivers(
    material_positions: Sequence[Mapping[str, Any]],
    top_industry_drivers: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for driver in top_industry_drivers:
        label = str(driver.get("label", ""))
        sector = _risk_driver_sector(label)
        position = next(
            (
                item
                for item in material_positions
                if item.get("category") == "Eq Sector" and str(item.get("label", "")).strip() == sector
            ),
            None,
        )
        if position is None:
            continue
        matched.append(
            {
                "risk_driver": label,
                "mapped_sector": sector,
                "share_of_variance_pct": driver.get("share_of_variance_pct"),
                "active_weight": _round_or_none(position.get("active_weight"), 2),
                "signal_alignment": position.get("signal_alignment", ""),
                "top_sector_holdings": _top_security_slice(position.get("source_breakdown", {}), limit=3),
                "inference_level": "sector_proxy",
            }
        )
    return matched


def _specific_risk_watchlist(material_positions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        [item for item in material_positions if item.get("source_breakdown", {}).get("securities")],
        key=lambda item: abs(float(item.get("active_weight", 0.0))),
        reverse=True,
    )
    watchlist = []
    for item in ranked[:5]:
        watchlist.append(
            {
                "label": item.get("label", ""),
                "category": item.get("category", ""),
                "active_weight": _round_or_none(item.get("active_weight"), 2),
                "top_sector_holdings": _top_security_slice(item.get("source_breakdown", {}), limit=3),
                "inference_level": "sector_proxy",
            }
        )
    return watchlist


def _top_security_slice(source_breakdown: Mapping[str, Any], *, limit: int) -> list[dict[str, Any]]:
    securities = list(source_breakdown.get("securities", []))
    sliced = []
    for security in securities[:limit]:
        sliced.append(
            {
                "security_name": security.get("security_name", ""),
                "portfolio_weight": _round_or_none(security.get("portfolio_weight"), 2),
                "benchmark_weight": _round_or_none(security.get("benchmark_weight"), 2),
                "active_weight": _round_or_none(security.get("active_weight"), 2),
            }
        )
    return sliced


def _risk_change_block(latest_row: Mapping[str, Any], prior_row: Mapping[str, Any] | None) -> dict[str, Any]:
    if prior_row is None:
        return {}
    fields = {
        "active_predicted_risk_change_pct": "Active Predicted Risk",
        "active_share_change_pct": "Active Share",
        "active_factor_risk_change_pct": "Active Factor Risk",
        "active_specific_risk_change_pct": "Active Specific Risk",
        "active_style_factor_risk_change_pct": "Active Style Factor Risk",
        "active_industry_factor_risk_change_pct": "Active Industry Factor Risk",
        "active_market_factor_risk_change_pct": "Active Market Factor Risk",
    }
    return {
        output_name: _pct_delta(latest_row.get(field_name), prior_row.get(field_name))
        for output_name, field_name in fields.items()
    }


def _narrative_observations(
    *,
    summary: Mapping[str, Any],
    top_style: Sequence[Mapping[str, Any]],
    top_industry: Sequence[Mapping[str, Any]],
    return_mtd: Mapping[str, Any],
    holdings_contributors: Sequence[Mapping[str, Any]],
    specific_watchlist: Sequence[Mapping[str, Any]],
) -> list[str]:
    observations: list[str] = []
    measured_buckets = {
        "style": summary.get("active_style_factor_risk_pct"),
        "industry": summary.get("active_industry_factor_risk_pct"),
        "market": summary.get("active_market_factor_risk_pct"),
        "specific": summary.get("active_specific_risk_pct"),
    }
    leading_bucket = max(measured_buckets.items(), key=lambda item: item[1] or float("-inf"))
    if leading_bucket[1] is not None:
        observations.append(
            f"Measured active risk is currently most concentrated in {leading_bucket[0]} risk at {leading_bucket[1]:.2f}%."
        )
    if top_industry:
        leader = top_industry[0]
        observations.append(
            f"The biggest modeled industry driver is {leader['label']} at {leader['share_of_variance_pct']:.1f}% of active variance."
        )
    if top_style:
        leader = top_style[0]
        observations.append(
            f"The largest modeled style driver is {leader['label']} at {leader['share_of_variance_pct']:.1f}% of active variance."
        )
    if return_mtd:
        factor = return_mtd.get("active_factor_return_pct")
        specific = return_mtd.get("active_specific_return_pct")
        if factor is not None and specific is not None:
            stronger = "factor" if factor >= specific else "specific"
            observations.append(
                f"Month-to-date active performance has been led more by {stronger} return ({factor:.2f}% factor vs {specific:.2f}% specific)."
            )
    if holdings_contributors:
        leader = holdings_contributors[0]
        security_names = [
            security["security_name"]
            for security in leader.get("top_sector_holdings", [])
            if security.get("security_name")
        ]
        if security_names:
            observations.append(
                f"Within the mapped {leader['mapped_sector']} bucket behind {leader['risk_driver']} risk, the largest sector holdings are {', '.join(security_names[:3])}."
            )
    elif specific_watchlist:
        leader = specific_watchlist[0]
        observations.append(
            f"Specific risk likely matters most in {leader['label']}, where the active position is {leader['active_weight']:.2f} pts."
        )
    return observations


def _canonical_return_name(field: str) -> str:
    return (
        field.lower()
        .replace("(", "")
        .replace(")", "")
        .replace("%", "pct")
        .replace("-", "_")
        .replace(" ", "_")
    )


def _risk_driver_sector(label: str) -> str:
    if label in INDUSTRY_TO_SECTOR:
        return INDUSTRY_TO_SECTOR[label]
    if "Software" in label or "Semiconductor" in label or "Technology" in label:
        return "Information Technology"
    if "Bank" in label or "Finance" in label or "Insurance" in label:
        return "Financials"
    if "Health" in label or "Pharma" in label or "Biotech" in label:
        return "Health Care"
    if "Utility" in label:
        return "Utilities"
    return label


def _pct(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value) * 100.0, 2)


def _pct_delta(current: Any, prior: Any) -> float | None:
    if current is None or prior is None:
        return None
    return round((float(current) - float(prior)) * 100.0, 2)


def _round_or_none(value: Any, digits: int) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(round(float(value)))


__all__ = [
    "RiskReportParseResult",
    "build_risk_context",
    "parse_risk_report_workbook",
]
