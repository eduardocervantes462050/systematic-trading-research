import os
import glob
from datetime import datetime
import subprocess
import json

# -----------------------
# Paths
# -----------------------
interim_dir = "data/interim"  # where *_features.csv are
figures_dir = "reports/figures"  # where PNGs are
os.makedirs(figures_dir, exist_ok=True)

report_template = "C:\\Users\\eduar\\Projects\\Python\\quant_project\\reports\\quantitative_portfolio_report_template.md"
report_md = "C:\\Users\\eduar\\Projects\\Python\\quant_project\\reports\\quantitative_portfolio_report.md"
report_pdf = "C:\\Users\\eduar\\Projects\\Python\\quant_project\\reports\\quantitative_portfolio_report.pdf"
weights_file = (
    "C:\\Users\\eduar\\Projects\\Python\\quant_project\\reports\\ef_weights.json"
)
# -----------------------
# STEP 0: Example portfolio weights and metrics
# -----------------------
# In practice, these should come from your portfolio calculation
with open(weights_file, "r", encoding="utf-8") as f:
    portfolio_weights = json.load(f)
    print(f"Loaded portfolio weights: {portfolio_weights}")

key_metrics = {
    "cagr": "12.5%",
    "sharpe": "1.45",
    "max_drawdown": "-15%",
    "start_date": "2000-01-01",
    "end_date": "2025-12-31",
    "fred_series": "CPIAUCSL",
}

# # -----------------------
# # STEP 1: Build Markdown for portfolio allocation table
# # -----------------------
# allocation_md = "| Ticker | Weight |\n|--------|--------|\n"
# for ticker, weight in portfolio_weights.items():
#     allocation_md += f"| {ticker} | {weight*100:.1f}% |\n"

# # -----------------------
# # STEP 2: Build Markdown for individual ticker plots
# # -----------------------
# tickers_files = glob.glob(os.path.join(interim_dir, "*_features.csv"))
# tickers = [os.path.basename(f).split("_")[0] for f in tickers_files]

# markdown_plots = ""
# for ticker in tickers:
#     figures = glob.glob(os.path.join(figures_dir, f"{ticker}*.png"))
#     if figures:
#         markdown_plots += f"## {ticker}\n\n"
#         for fig_path in figures:
#             fig_name = os.path.basename(fig_path)
#             markdown_plots += f"![{fig_name}](figures/{fig_name})\n\n"

# # -----------------------
# # STEP 3: Include main portfolio plots
# # -----------------------
# # Expected filenames (adjust as needed)
# main_plots = {
#     "equity_curve": "portfolio_equity.png",
#     "drawdown": "portfolio_drawdown.png",
#     "allocation": "portfolio_allocation.png",
# }

# portfolio_plots_md = ""
# for desc, fname in main_plots.items():
#     path = os.path.join(figures_dir, fname)
#     if os.path.exists(path):
#         portfolio_plots_md += f"### {desc.replace('_',' ').title()}\n"
#         portfolio_plots_md += f"![{fname}](figures/{fname})\n\n"

# # -----------------------
# # STEP 4: Load Markdown template
# # -----------------------
# with open(report_template, "r", encoding="utf-8") as f:
#     template = f.read()

# # -----------------------
# # STEP 5: Replace placeholders
# # -----------------------
# placeholders = {
#     "{{date}}": datetime.today().strftime("%Y-%m-%d"),
#     "{{tickers}}": ", ".join(portfolio_weights.keys()),
#     "{{start_date}}": key_metrics["start_date"],
#     "{{end_date}}": key_metrics["end_date"],
#     "{{cagr}}": key_metrics["cagr"],
#     "{{sharpe}}": key_metrics["sharpe"],
#     "{{max_drawdown}}": key_metrics["max_drawdown"],
#     "{{fred_series}}": key_metrics["fred_series"],
#     "{{allocation_table}}": allocation_md,
#     "{{portfolio_plots}}": portfolio_plots_md,
#     "{{plots_per_ticker}}": markdown_plots,
# }

# for key, val in placeholders.items():
#     template = template.replace(key, str(val))

# # -----------------------
# # STEP 6: Write Markdown report
# # -----------------------
# with open(report_md, "w") as f:
#     f.write(template)

# print(f"Markdown report generated: {report_md}")

# # -----------------------
# # STEP 7: Convert to PDF (if Pandoc installed)
# # -----------------------
# try:
#     subprocess.run(
#         ["pandoc", report_md, "-o", report_pdf, "--pdf-engine=xelatex"], check=True
#     )
#     print(f"PDF report generated: {report_pdf}")
# except FileNotFoundError:
#     print("Pandoc not found. Install Pandoc to convert Markdown to PDF.")
# except subprocess.CalledProcessError:
#     print("Pandoc failed to generate PDF. Check your Pandoc/LaTeX installation.")
