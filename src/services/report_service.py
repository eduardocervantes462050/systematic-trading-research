from pathlib import Path
from datetime import datetime

from data.models import Portfolio, PortfolioAsset


# ─────────────────────────────────────────────
# PATH CONFIG
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = BASE_DIR / "reports" / "client_portfolio_template.md"
OUTPUT_DIR = BASE_DIR / "reports"


# ─────────────────────────────────────────────
# MAIN REPORT GENERATOR
# ─────────────────────────────────────────────

def generate_client_portfolio_report(session, client_id: str) -> str:
    """
    Generates a markdown report showing:
    - Client portfolios
    - Portfolio holdings (PortfolioAsset → Asset)
    """

    # ─────────────────────────────────────────
    # 1. Load portfolios
    # ─────────────────────────────────────────
    portfolios = (
        session.query(Portfolio)
        .filter(Portfolio.client_id == client_id)
        .all()
    )

    # ─────────────────────────────────────────
    # 2. Build holdings section
    # ─────────────────────────────────────────
    report_body = ""

    if not portfolios:
        report_body = "No portfolios found for this client."
    else:
        for portfolio in portfolios:
            report_body += f"\n## {portfolio.name}\n\n"
            report_body += "| Symbol | Quantity | Avg Price |\n"
            report_body += "|--------|----------|-----------|\n"

            holdings = (
                session.query(PortfolioAsset)
                .filter(PortfolioAsset.portfolio_id == portfolio.portfolio_id)
                .all()
            )

            if not holdings:
                report_body += "| - | - | - |\n\n"
                continue

            for h in holdings:

                # ── SAFE SYMBOL RESOLUTION ──
                symbol = None
                if h.asset:
                    symbol = getattr(h.asset, "symbol", None) or getattr(h.asset, "ticker", None)

                symbol = symbol or str(h.asset_id)

                report_body += (
                    f"| {symbol} | "
                    f"{float(h.quantity):.4f} | "
                    f"{float(h.avg_price) if h.avg_price else 0:.2f} |\n"
                )

            report_body += "\n"

    # ─────────────────────────────────────────
    # 3. Load template
    # ─────────────────────────────────────────
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # ─────────────────────────────────────────
    # 4. Fill placeholders
    # ─────────────────────────────────────────
    placeholders = {
        "{{date}}": datetime.today().strftime("%Y-%m-%d"),
        "{{client_id}}": client_id,
        "{{portfolio_table}}": report_body,
        "{{portfolio_count}}": str(len(portfolios)),
    }

    for key, value in placeholders.items():
        template = template.replace(key, str(value))

    # ─────────────────────────────────────────
    # 5. Save output file
    # ─────────────────────────────────────────
    output_path = OUTPUT_DIR / f"client_{client_id}_portfolio_report.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)

    return str(output_path)