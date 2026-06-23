from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from db.session import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, nullable=False)
    repo = Column(String, nullable=False)
    commit_sha = Column(String, nullable=False)
    verdict = Column(String, nullable=False)          # "issues_found" / "clean"
    findings = Column(JSON, nullable=True)            # raw list of findings
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String, nullable=True)
