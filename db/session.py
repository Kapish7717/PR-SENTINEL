import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime , timedelta
# Fall back to a local sqlite database for easy development/testing
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./pr_sentinel.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def cleanup_old_reviews(db):
    """
    Deletes reviews older than 30 days.
    """
    from db.models import Review
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted_count = db.query(Review).filter(Review.reviewed_at < cutoff_date).delete()
        db.commit()
        print(f"Database cleanup: Deleted {deleted_count} logs older than 30 days.")
    except Exception as e:
        print(f"Failed to run database cleanup: {e}")