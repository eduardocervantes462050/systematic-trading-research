from data.engine import build_db, get_session
from services.report_service import generate_client_portfolio_report

engine, SessionFactory = build_db()

client_id = "75b67544-63dd-4110-b994-cdf4382445ba"

with get_session(SessionFactory) as session:
    path = generate_client_portfolio_report(session, client_id)

print("Generated:", path)