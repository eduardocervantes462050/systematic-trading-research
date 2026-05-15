"""
Generate a quantitative portfolio report for an optimized portfolio.
 
Usage:
    python -m quantitative_portfolio_report "<portfolio_name>" <method>
 
Examples:
    python -m quantitative_portfolio_report "Global Multi-Asset Growth Portfolio" equal_weight
    python -m quantitative_portfolio_report "Global Multi-Asset Growth Portfolio" max_sharpe
    python -m quantitative_portfolio_report "Global Multi-Asset Growth Portfolio" risk_parity
"""
 
import os
import sys
import json
from datetime import datetime
 
from data.engine import build_db, get_session
from data.models import Portfolio
from data.models.optimized import OptimizedPortfolio, OptimizedPortfolioMetrics
from data.repositories.optimized_repo import (
    get_optimized_portfolio_by_method,
    get_weights,
)
from portfolio.metrics.optimized_metrics import (
    calculate_and_store_optimized_cagr,
    calculate_and_store_optimized_volatility,
    calculate_and_store_optimized_max_drawdown,
    calculate_and_store_optimized_sharpe,
)
 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 
TEMPLATE_PATH = os.path.join(
    BASE_DIR, "reports", "quantitative_portfolio_report_template.md"
)
FIGURES_DIR = os.path.join(BASE_DIR, "reports", "figures")
 
 
# =============================================================================
# HELPERS
# =============================================================================
 
def get_optimized_metric(session, optimized_portfolio_id, metric_type):
    record = (
        session.query(OptimizedPortfolioMetrics)
        .filter(
            OptimizedPortfolioMetrics.optimized_portfolio_id == optimized_portfolio_id,
            OptimizedPortfolioMetrics.metric_type == metric_type,
        )
        .first()
    )
    return float(record.value) if record else None
 
 
# =============================================================================
# REPORT GENERATOR
# =============================================================================
 
def generate_report(portfolio_name: str, method: str):
    engine, SessionFactory = build_db()
 
    with get_session(SessionFactory) as session:
 
        # 1. Look up base portfolio
        portfolio = session.query(Portfolio).filter_by(name=portfolio_name).first()
        if not portfolio:
            print(f"Portfolio '{portfolio_name}' not found in database.")
            return
 
        # 2. Look up optimized portfolio
        opt = get_optimized_portfolio_by_method(
            session, portfolio.portfolio_id, method
        )
        if not opt:
            print(
                f"No optimized portfolio found for '{portfolio_name}' "
                f"with method '{method}'.\n"
                f"Run the optimizer first:\n"
                f"  python -m cli.main --portfolio_name \"{portfolio_name}\" "
                f"--strategy {method} --method {method}"
            )
            return
 
        opt_id = opt.optimized_portfolio_id
        print(f"Generating report for: {portfolio_name} — {method}")
 
        # 3. Compute and store metrics
        print("Calculating metrics...")
        calculate_and_store_optimized_cagr(session)
        calculate_and_store_optimized_volatility(session)
        calculate_and_store_optimized_max_drawdown(session)
        calculate_and_store_optimized_sharpe(session)
 
        # 4. Pull metrics from DB
        cagr         = get_optimized_metric(session, opt_id, "CAGR")
        sharpe       = get_optimized_metric(session, opt_id, "SHARPE")
        max_drawdown = get_optimized_metric(session, opt_id, "MAX_DRAWDOWN")
        volatility   = get_optimized_metric(session, opt_id, "VOLATILITY")
 
        # 5. Date range from CAGR record
        cagr_record = (
            session.query(OptimizedPortfolioMetrics)
            .filter_by(optimized_portfolio_id=opt_id, metric_type="CAGR")
            .first()
        )
        start_date = str(cagr_record.start_date) if cagr_record else "N/A"
        end_date   = str(cagr_record.end_date)   if cagr_record else "N/A"
 
        # 6. Load weights from DB
        weights = get_weights(session, opt_id)
        tickers = ", ".join(weights.keys())
 
        # 7. Build allocation table
        allocation_md = "| Ticker | Weight |\n|--------|--------|\n"
        for ticker, weight in weights.items():
            allocation_md += f"| {ticker} | {weight * 100:.1f}% |\n"
 
        # 8. Build plots section
        plots_md = ""
        for ticker in weights.keys():
            plots_md += f"## {ticker}\n\n"
            for fig in ["signals", "rolling_stats", "returns_hist"]:
                path = os.path.join(FIGURES_DIR, f"{ticker}_{fig}.png")
                if os.path.exists(path):
                    plots_md += f"![{ticker} {fig}](figures/{ticker}_{fig}.png)\n\n"
 
        # 9. Load template
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = f.read()
 
        # 10. Fill placeholders
        report_title = f"{portfolio_name} — {method.replace('_', ' ').title()}"
        placeholders = {
            "{{date}}":             datetime.today().strftime("%Y-%m-%d"),
            "{{portfolio_name}}":   report_title,
            "{{tickers}}":          tickers,
            "{{start_date}}":       start_date,
            "{{end_date}}":         end_date,
            "{{cagr}}":             f"{cagr:.2%}"         if cagr         is not None else "N/A",
            "{{sharpe}}":           f"{sharpe:.2f}"        if sharpe       is not None else "N/A",
            "{{max_drawdown}}":     f"{max_drawdown:.2%}"  if max_drawdown is not None else "N/A",
            "{{volatility}}":       f"{volatility:.2%}"    if volatility   is not None else "N/A",
            "{{fred_series}}":      "CPIAUCSL",
            "{{allocation_table}}": allocation_md,
            "{{portfolio_plots}}":  "",
            "{{plots_per_ticker}}": plots_md,
        }
 
        for key, val in placeholders.items():
            template = template.replace(key, str(val))
 
        # 11. Write report
        safe_name = f"{portfolio_name}_{method}"
        report_path = os.path.join(
            BASE_DIR, "reports", f"{safe_name}_quantitative_portfolio_report.md"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(template)
 
        # 12. Print summary
        print(f"\nReport generated: {report_path}")
        print(f"  Method:       {method}")
        print(f"  CAGR:         {cagr:.2%}"         if cagr         is not None else "  CAGR:         N/A")
        print(f"  Sharpe:       {sharpe:.2f}"        if sharpe       is not None else "  Sharpe:       N/A")
        print(f"  Max Drawdown: {max_drawdown:.2%}"  if max_drawdown is not None else "  Max Drawdown: N/A")
        print(f"  Volatility:   {volatility:.2%}"    if volatility   is not None else "  Volatility:   N/A")
 
 
# =============================================================================
# ENTRY POINT
# =============================================================================
 
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:   python -m quantitative_portfolio_report \"<portfolio_name>\" <method>")
        print()
        print("Methods: equal_weight | max_sharpe | min_vol | inverse_vol | risk_parity")
        print()
        print("Example: python -m quantitative_portfolio_report \"Global Multi-Asset Growth Portfolio\" equal_weight")
        sys.exit(1)
 
    # last arg is method, everything before is portfolio name
    *name_parts, method = sys.argv[1:]
    portfolio_name = " ".join(name_parts)
    generate_report(portfolio_name, method)
 
