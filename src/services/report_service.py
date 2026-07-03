from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from data.models import Portfolio, PortfolioAsset,PortfolioMetrics



# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = BASE_DIR / "reports" / "templates"
OUTPUT_DIR = BASE_DIR / "reports" / "outputs"


# ─────────────────────────────────────────────
# METRICS FETCH
# ─────────────────────────────────────────────

def get_latest_metrics(session, portfolio_id: str):
    rows = (
        session.query(PortfolioMetrics)
        .filter(PortfolioMetrics.portfolio_id == portfolio_id)
        .all()
    )

    if not rows:
        return {}

    metrics = {}

    for r in rows:
        if not r.metric_type:
            continue

        metrics[r.metric_type] = r.value

    return metrics


# ─────────────────────────────────────────────
# MAIN REPORT
# ─────────────────────────────────────────────

def generate_client_portfolio_report(session, client_id: str) -> str:

    portfolios = (
        session.query(Portfolio)
        .filter(Portfolio.client_id == client_id)
        .all()
    )

    # ─────────────────────────────
    # BUILD STRUCTURED DATA
    # ─────────────────────────────

    portfolio_data = []

    for p in portfolios:

        holdings = (
            session.query(PortfolioAsset)
            .filter(PortfolioAsset.portfolio_id == p.portfolio_id)
            .all()
        )

        holdings_list = []

        for h in holdings:
            symbol = None
            if h.asset:
                symbol = getattr(h.asset, "symbol", None) or getattr(h.asset, "ticker", None)

            holdings_list.append({
                "symbol": symbol or str(h.asset_id),
                "quantity": float(h.quantity),
                "avg_price": float(h.avg_price or 0),
            })

        portfolio_data.append({
            "name": p.name,
            "holdings": holdings_list,
            "metrics": get_latest_metrics(session, p.portfolio_id),
        })

    # ─────────────────────────────
    # JINJA ENV
    # ─────────────────────────────

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("client_portfolio_template.md")

    # ─────────────────────────────
    # RENDER
    # ─────────────────────────────

    rendered = template.render(
        client_id=client_id,
        date=datetime.today().strftime("%Y-%m-%d"),
        portfolios=portfolio_data,
    )

    # ─────────────────────────────
    # SAVE
    # ─────────────────────────────

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"client_{client_id}_portfolio_report.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    return str(output_path)