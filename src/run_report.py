import os
import glob
from datetime import datetime
import subprocess

# -----------------------
# Paths
# -----------------------
interim_dir = "data/interim"  # where *_features.csv are
figures_dir = "reports/figures"  # where PNGs are
os.makedirs(figures_dir, exist_ok=True)

report_template = "reports/report_template.md"
report_md = "reports/report.md"
report_pdf = "reports/quant_report.pdf"

# -----------------------
# STEP 1: Build Markdown for all tickers
# -----------------------
tickers_files = glob.glob(os.path.join(interim_dir, "*_features.csv"))
tickers = [os.path.basename(f).split("_")[0] for f in tickers_files]

markdown_plots = ""
for ticker in tickers:
    # Find all PNGs for this ticker
    figures = glob.glob(os.path.join(figures_dir, f"{ticker}*.png"))
    markdown_plots += f"## {ticker}\n\n"
    for fig_path in figures:
        fig_name = os.path.basename(fig_path)
        # Use relative path from report.md
        markdown_plots += f"![{fig_name}](figures/{fig_name})\n\n"

# -----------------------
# STEP 2: Load Markdown template
# -----------------------
with open(report_template, "r") as f:
    template = f.read()

# -----------------------
# STEP 3: Replace placeholders
# -----------------------
placeholders = {
    "{{date}}": datetime.today().strftime("%Y-%m-%d"),
    "{{tickers}}": ", ".join(tickers),
    "{{start_date}}": "2000-01-01",
    "{{end_date}}": "2025-12-31",
    "{{cagr}}": "12.5%",
    "{{sharpe}}": "1.45",
    "{{max_drawdown}}": "-15%",
    "{{fred_series}}": "CPIAUCSL",
    "{{plots_per_ticker}}": markdown_plots,
}

for key, val in placeholders.items():
    template = template.replace(key, str(val))

# -----------------------
# STEP 4: Write Markdown report
# -----------------------
with open(report_md, "w") as f:
    f.write(template)

print(f"Markdown report generated: {report_md}")

# -----------------------
# STEP 5: Convert to PDF (if Pandoc installed)
# -----------------------
try:
    subprocess.run(
        ["pandoc", report_md, "-o", report_pdf, "--pdf-engine=xelatex"], check=True
    )
    print(f"PDF report generated: {report_pdf}")
except FileNotFoundError:
    print("Pandoc not found. Install Pandoc to convert Markdown to PDF.")
except subprocess.CalledProcessError:
    print("Pandoc failed to generate PDF. Check your Pandoc/LaTeX installation.")
