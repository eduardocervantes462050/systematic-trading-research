import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.data.engine import build_db

engine, SessionFactory = build_db()
print("✅ Database and tables created successfully!")