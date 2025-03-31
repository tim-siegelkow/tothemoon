from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL
from database.models import Base

# Create engine and session
engine = create_engine(DATABASE_URL)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)

def reset_db():
    """Drop all tables and recreate them - WARNING: This will delete all data."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
def get_session():
    """Get a new database session."""
    return Session()

def close_session(session):
    """Close a database session."""
    session.close()
    
def add_transaction(session, transaction):
    """Add a new transaction to the database."""
    # Add transaction to database
    session.add(transaction)
    session.commit()
    return transaction

def add_audit_log(session, audit_log):
    """Add a new audit log to the database."""
    session.add(audit_log)
    session.commit()
    return audit_log

def get_all_transactions(session, limit=None):
    """Get all transactions from the database."""
    from database.models import Transaction
    query = session.query(Transaction).order_by(Transaction.date.desc())
    if limit:
        query = query.limit(limit)
    return query.all()

def get_transaction_by_id(session, transaction_id):
    """Get a transaction by ID."""
    from database.models import Transaction
    return session.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()

def update_transaction_category(session, transaction_id, new_category, old_category=None):
    """Update a transaction's category and create an audit log."""
    from database.models import Transaction, AuditLog
    
    transaction = get_transaction_by_id(session, transaction_id)
    if not transaction:
        return None
    
    if old_category is None:
        old_category = transaction.user_verified_category or transaction.ai_suggested_category
    
    transaction.user_verified_category = new_category
    
    # Create audit log
    audit_log = AuditLog(
        transaction_id=transaction_id,
        old_category=old_category,
        new_category=new_category
    )
    
    session.add(audit_log)
    session.commit()
    
    return transaction
