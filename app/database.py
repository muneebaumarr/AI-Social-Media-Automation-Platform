import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Read with explicit defaults so we never get None
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "ai_social_media_db")

# Convert to str explicitly — prevents None causing quote_plus to crash
DB_PASSWORD = str(DB_PASSWORD) if DB_PASSWORD else ""
DB_USER     = str(DB_USER)     if DB_USER     else "root"

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # auto-reconnect if connection drops
    pool_recycle=3600,    # recycle connections every hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        print(f"   Connected to: {DB_NAME} on {DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   URL attempted: mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")