from pathlib import Path

from portfolio_analyst_agent.risk_report import build_risk_context, parse_risk_report_workbook


REPO_ROOT = Path(__file__).resolve().parents[1]
RISK_WORKBOOK = REPO_ROOT / "data" / "2026-05-31" / "weekly_US_EQ_Time Series Risk Report - Sortable_2026-03-31_2026-06-05.xlsx"


def test_parse_risk_report_workbook_smoke():
    result = parse_risk_report_workbook(RISK_WORKBOOK)

    assert result.settings["Portfolio"] == "US_EQ"
    assert result.settings["Benchmark"] == "Morningstar US Market TR USD"
    assert len(result.risk_details) >= 40
    assert result.risk_details[-1]["date"].isoformat() == "2026-06-08"


def test_build_risk_context_uses_latest_business_day_on_or_before_review_date():
    material_positions = [
        {
            "category": "Eq Sector",
            "label": "Information Technology",
            "active_weight": -7.62,
            "signal_alignment": "aligned",
            "source_breakdown": {
                "securities": [
                    {"security_name": "NVIDIA", "portfolio_weight": 1.1, "benchmark_weight": 2.8, "active_weight": -1.7},
                    {"security_name": "Microsoft", "portfolio_weight": 3.4, "benchmark_weight": 4.4, "active_weight": -1.0},
                ]
            },
        },
        {
            "category": "Eq Sector",
            "label": "Financials",
            "active_weight": 3.07,
            "signal_alignment": "aligned",
            "source_breakdown": {
                "securities": [
                    {"security_name": "Visa", "portfolio_weight": 1.0, "benchmark_weight": 0.3, "active_weight": 0.7},
                ]
            },
        },
    ]

    context = build_risk_context(
        RISK_WORKBOOK,
        review_date="2026-05-31",
        material_positions=material_positions,
    )

    assert context["available"] is True
    assert context["summary"]["risk_date_used"] == "2026-05-29"
    assert context["summary"]["active_predicted_risk_pct"] is not None
    assert context["top_industry_risk_drivers"]
    assert context["return_attribution_mtd"]["window_end"] == "2026-05-29"
    assert context["specific_risk_watchlist"]
