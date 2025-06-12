from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_role = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True) 