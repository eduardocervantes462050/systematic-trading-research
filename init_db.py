from src.data.database import build_db

engine, SessionFactory = build_db()
print("✅ Database and tables created successfully!")
