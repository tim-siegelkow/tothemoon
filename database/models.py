from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    transaction_id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    original_category = Column(String, nullable=True)
    ai_suggested_category = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    user_verified_category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    audit_logs = relationship("AuditLog", back_populates="transaction")
    
    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, date={self.date}, amount={self.amount})>"


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    log_id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.transaction_id'))
    old_category = Column(String, nullable=True)
    new_category = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    
    transaction = relationship("Transaction", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.log_id}, transaction_id={self.transaction_id})>"
