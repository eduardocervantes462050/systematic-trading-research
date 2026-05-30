"""
Run this from your project root to diagnose rebalance:
  python debug_rebalance.py
"""
from data.engine import build_db, get_session
from data.models.optimized import OptimizedPortfolio, OptimizedPortfolioAsset
from data.models.asset import Asset
import uuid
 
PORTFOLIO_ID = "02eee7b7-514e-4968-84ed-a2ab868e4b54"
 
engine, SessionFactory = build_db()
with get_session(SessionFactory) as session:
 
    # 1. Find latest optimized portfolio
    opt = (
        session.query(OptimizedPortfolio)
        .filter(OptimizedPortfolio.portfolio_id == uuid.UUID(PORTFOLIO_ID))
        .order_by(OptimizedPortfolio.created_at.desc())
        .first()
    )
    if not opt:
        print("❌ No OptimizedPortfolio found for this portfolio_id")
    else:
        print(f"✓ OptimizedPortfolio found: {opt.name}  id={opt.optimized_portfolio_id}")
 
        # 2. Check optimized_portfolio_assets rows
        rows = (
            session.query(OptimizedPortfolioAsset, Asset)
            .join(Asset, OptimizedPortfolioAsset.asset_id == Asset.asset_id)
            .filter(OptimizedPortfolioAsset.optimized_portfolio_id == opt.optimized_portfolio_id)
            .all()
        )
        if not rows:
            print("❌ No rows in optimized_portfolio_assets for this run")
            print("   → optimize is printing weights but NOT saving them to the DB")
        else:
            print(f"✓ Found {len(rows)} weight row(s):")
            for opa, asset in rows:
                print(f"   {asset.symbol}: {float(opa.weight):.4f}")
 
        # 3. Check latest prices
        print("\nChecking latest prices...")
        for symbol in ["AAPL", "GOOGL", "MSFT"]:
            asset = session.query(Asset).filter(Asset.symbol == symbol).first()
            if not asset:
                print(f"  ❌ {symbol}: asset not found")
                continue
            from data.models.asset import AssetPrice
            latest = (
                session.query(AssetPrice)
                .filter(AssetPrice.asset_id == asset.asset_id)
                .order_by(AssetPrice.price_date.desc())
                .first()
            )
            if latest:
                print(f"  ✓ {symbol}: latest close={latest.close}  date={latest.price_date}")
            else:
                print(f"  ❌ {symbol}: no price data")
