"""
src/Graphs/plot_equity_curve.py

Plot and save equity curves for both base and optimized portfolios.

Base portfolios:
    - Reads from portfolio_equity_curves table (pre-computed, stored)

Optimized portfolios:
    - Computed on the fly from weights + price history
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session

from data.models import PortfolioEquityCurve
from data.repositories.optimized_repo import get_weights, get_optimized_portfolio_by_method
from portfolio.optimized_equity_curve import calculate_optimized_equity_curve

# Save directory — always resolves to reports/figures/ at project root
FIGURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "reports",
    "figures",
)


# =============================================================================
# HELPERS
# =============================================================================

def _safe_name(name: str) -> str:
    """Convert a name to a safe filename."""
    return name.replace(" ", "_").replace("/", "_").replace("\\", "_")


def _save_figure(fig, filename: str):
    """Save figure to reports/figures/."""
    os.makedirs(FIGURES_DIR, exist_ok=True)
    path = os.path.join(FIGURES_DIR, f"{_safe_name(filename)}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"Saved: {path}")


# =============================================================================
# BASE PORTFOLIO — reads from portfolio_equity_curves table
# =============================================================================

def get_equity_curve(session: Session, portfolio_id) -> pd.DataFrame:
    """Load equity curve from DB for a base portfolio."""
    rows = (
        session.query(PortfolioEquityCurve)
        .filter(PortfolioEquityCurve.portfolio_id == portfolio_id)
        .order_by(PortfolioEquityCurve.date)
        .all()
    )
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [{"date": r.date, "total_value": float(r.total_value)} for r in rows]
    )


def plot_equity_curve(
    session: Session,
    portfolio_id,
    portfolio_name: str = "Portfolio",
    show: bool = True,
    save: bool = True,
):
    """
    Plot equity curve for a single base portfolio.

    Parameters
    ----------
    session : Session
    portfolio_id : UUID
    portfolio_name : str
    show : bool   — display interactively (default True)
    save : bool   — save to reports/figures/ (default True)
    """
    df = get_equity_curve(session, portfolio_id)

    if df.empty:
        print(f"No equity curve data for '{portfolio_name}'")
        return

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["date"], df["total_value"], linewidth=1.5, color="#2196F3")
    ax.set_title(f"Equity Curve — {portfolio_name}", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save:
        _save_figure(fig, f"{portfolio_name}_equity_curve")

    if show:
        plt.show()

    plt.close(fig)


def plot_multiple_equity_curves(
    session: Session,
    portfolios: list[tuple],
    title: str = "Equity Curve Comparison",
    filename: str = "comparison_equity_curve",
    show: bool = True,
    save: bool = True,
):
    """
    Plot equity curves for multiple base portfolios on one chart.

    Parameters
    ----------
    portfolios : list of (portfolio_id, portfolio_name)
    title : str
    filename : str   — output filename without extension
    show : bool
    save : bool
    """
    fig, ax = plt.subplots(figsize=(12, 5))
    any_data = False

    for portfolio_id, name in portfolios:
        df = get_equity_curve(session, portfolio_id)
        if df.empty:
            print(f"No equity curve data for '{name}', skipping")
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        ax.plot(df["date"], df["total_value"], label=name, linewidth=1.5)
        any_data = True

    if not any_data:
        print("No data to plot")
        plt.close(fig)
        return

    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save:
        _save_figure(fig, filename)

    if show:
        plt.show()

    plt.close(fig)


# =============================================================================
# OPTIMIZED PORTFOLIO — computed from weights + price history
# =============================================================================

def get_optimized_equity_curve(session: Session, optimized_portfolio_id) -> pd.DataFrame:
    """Compute equity curve for an optimized portfolio."""
    df = calculate_optimized_equity_curve(session, optimized_portfolio_id)
    if df.empty:
        return pd.DataFrame()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    return df


def plot_optimized_equity_curve(
    session: Session,
    optimized_portfolio_id,
    portfolio_name: str = "Portfolio",
    method: str = "",
    show: bool = True,
    save: bool = True,
):
    """
    Plot equity curve for a single optimized portfolio.

    Parameters
    ----------
    session : Session
    optimized_portfolio_id : UUID
    portfolio_name : str   — base portfolio name
    method : str           — optimization method label (e.g. "max_sharpe")
    show : bool
    save : bool
    """
    df = get_optimized_equity_curve(session, optimized_portfolio_id)

    if df.empty:
        print(f"No equity curve data for '{portfolio_name}' ({method})")
        return

    label = f"{portfolio_name} — {method.replace('_', ' ').title()}" if method else portfolio_name

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["Date"], df["total_value"], linewidth=1.5, color="#4CAF50")
    ax.set_title(f"Equity Curve — {label}", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Portfolio Value")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save:
        _save_figure(fig, f"{portfolio_name}_{method}_equity_curve")

    if show:
        plt.show()

    plt.close(fig)


def plot_multiple_optimized_equity_curves(
    session: Session,
    optimized_portfolios: list[tuple],
    title: str = "Optimized Portfolio Comparison",
    filename: str = "optimized_comparison_equity_curve",
    show: bool = True,
    save: bool = True,
):
    """
    Plot equity curves for multiple optimized portfolios on one chart.
    Useful for comparing strategies side by side.

    Parameters
    ----------
    optimized_portfolios : list of (optimized_portfolio_id, label)
        e.g. [(uuid1, "Equal Weight"), (uuid2, "Max Sharpe")]
    title : str
    filename : str
    show : bool
    save : bool
    """
    fig, ax = plt.subplots(figsize=(12, 5))
    any_data = False

    for optimized_portfolio_id, label in optimized_portfolios:
        df = get_optimized_equity_curve(session, optimized_portfolio_id)
        if df.empty:
            print(f"No equity curve data for '{label}', skipping")
            continue
        ax.plot(df["Date"], df["total_value"], label=label, linewidth=1.5)
        any_data = True

    if not any_data:
        print("No data to plot")
        plt.close(fig)
        return

    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Portfolio Value")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save:
        _save_figure(fig, filename)

    if show:
        plt.show()

    plt.close(fig)