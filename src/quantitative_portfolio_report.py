import os
import sys
import json
from datetime import datetime
from data.database import build_db, get_session, Portfolio, PortfolioMetrics
from portfolio.metrics.cagr import calculate_and_store_cagr
from portfolio.metrics.volatility import calculate_and_store_volatility
from portfolio.metrics.max_drawdown import calculate_and_store_max_drawdown
from portfolio.metrics.sharpe import calculate_and_store_sharpe

# Base path — always points to project root regardless of where you run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE_PATH = os.path.join(
    BASE_DIR, "reports", "quantitative_portfolio_report_template.md"
)
FIGURES_DIR = os.path.join(BASE_DIR, "reports", "figures")
WEIGHTS_FILE = os.path.join(BASE_DIR, "reports", "ef_weights.json")


def get_metric(session, portfolio_id, metric_type):
    record = (
        session.query(PortfolioMetrics)
        .filter(
            PortfolioMetrics.portfolio_id == portfolio_id,
            PortfolioMetrics.metric_type == metric_type,
        )
        .first()
    )
    return float(record.value) if record else None


def generate_report(portfolio_name):
    engine, SessionFactory = build_db()

    with get_session(SessionFactory) as session:
        # 1. Get specific portfolio
        portfolio = session.query(Portfolio).filter_by(name=portfolio_name).first()
        if not portfolio:
            print(f"Portfolio '{portfolio_name}' not found in database.")
            return

        portfolio_id = portfolio.portfolio_id
        print(f"Generating report for: {portfolio.name}")

        # 2. Calculate and store all metrics
        print("Calculating metrics...")
        calculate_and_store_cagr(session)
        calculate_and_store_volatility(session)
        calculate_and_store_max_drawdown(session)
        calculate_and_store_sharpe(session)

        # 3. Pull metrics from DB
        cagr = get_metric(session, portfolio_id, "CAGR")
        sharpe = get_metric(session, portfolio_id, "SHARPE")
        max_drawdown = get_metric(session, portfolio_id, "MAX_DRAWDOWN")
        volatility = get_metric(session, portfolio_id, "VOLATILITY")

        # 4. Get date range
        cagr_record = (
            session.query(PortfolioMetrics)
            .filter(
                PortfolioMetrics.portfolio_id == portfolio_id,
                PortfolioMetrics.metric_type == "CAGR",
            )
            .first()
        )
        start_date = str(cagr_record.start_date) if cagr_record else "N/A"
        end_date = str(cagr_record.end_date) if cagr_record else "N/A"

        # 5. Load portfolio weights
        with open(WEIGHTS_FILE, "r") as f:
            portfolio_weights = json.load(f)

        tickers = ", ".join(portfolio_weights.keys())

        # 6. Build allocation table
        allocation_md = "| Ticker | Weight |\n|--------|--------|\n"
        for ticker, weight in portfolio_weights.items():
            allocation_md += f"| {ticker} | {weight * 100:.1f}% |\n"

        # 7. Build plots section per ticker
        plots_md = ""
        for ticker in portfolio_weights.keys():
            plots_md += f"## {ticker}\n\n"
            for fig in ["signals", "rolling_stats", "returns_hist"]:
                path = os.path.join(FIGURES_DIR, f"{ticker}_{fig}.png")
                if os.path.exists(path):
                    plots_md += f"![{ticker} {fig}](figures/{ticker}_{fig}.png)\n\n"

        # 8. Load template
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = f.read()

        # 9. Fill placeholders
        placeholders = {
            "{{date}}": datetime.today().strftime("%Y-%m-%d"),
            "{{portfolio_name}}": portfolio_name,
            "{{tickers}}": tickers,
            "{{start_date}}": start_date,
            "{{end_date}}": end_date,
            "{{cagr}}": f"{cagr:.2%}" if cagr is not None else "N/A",
            "{{sharpe}}": f"{sharpe:.2f}" if sharpe is not None else "N/A",
            "{{max_drawdown}}": (
                f"{max_drawdown:.2%}" if max_drawdown is not None else "N/A"
            ),
            "{{volatility}}": f"{volatility:.2%}" if volatility is not None else "N/A",
            "{{fred_series}}": "CPIAUCSL",
            "{{allocation_table}}": allocation_md,
            "{{portfolio_plots}}": "",
            "{{plots_per_ticker}}": plots_md,
        }

        for key, val in placeholders.items():
            template = template.replace(key, str(val))

        # 10. Write report
        report_md = os.path.join(
            BASE_DIR, "reports", f"{portfolio_name}_quantitative_portfolio_report.md"
        )
        with open(report_md, "w", encoding="utf-8") as f:
            f.write(template)

        print(f"\nReport generated: {report_md}")
        print(
            f"  CAGR:         {cagr:.2%}" if cagr is not None else "  CAGR:         N/A"
        )
        print(
            f"  Sharpe:       {sharpe:.2f}"
            if sharpe is not None
            else "  Sharpe:       N/A"
        )
        print(
            f"  Max Drawdown: {max_drawdown:.2%}"
            if max_drawdown is not None
            else "  Max Drawdown: N/A"
        )
        print(
            f"  Volatility:   {volatility:.2%}"
            if volatility is not None
            else "  Volatility:   N/A"
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quantitative_portfolio_report.py <portfolio_name>")
        print(
            "Example: python quantitative_portfolio_report.py Global Multi-Asset Growth Portfolio"
        )
    else:
        portfolio_name = " ".join(sys.argv[1:])
        generate_report(portfolio_name)
