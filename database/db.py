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

def delete_transactions_from_date(session, from_date):
    """Delete all transactions from a specific date onward.
    
    Args:
        session: The database session
        from_date: The date from which to delete transactions (inclusive)
        
    Returns:
        int: The number of transactions deleted
    """
    from database.models import Transaction
    from sqlalchemy import func
    
    # First count how many will be deleted
    count = session.query(func.count(Transaction.transaction_id)).filter(
        Transaction.date >= from_date
    ).scalar()
    
    # Then delete the transactions
    session.query(Transaction).filter(
        Transaction.date >= from_date
    ).delete(synchronize_session=False)
    
    # Commit the changes
    session.commit()
    
    return count

def delete_transactions_by_import_date(session, from_import_date, to_import_date=None):
    """Delete all transactions that were imported within a specific date range.
    
    Args:
        session: The database session
        from_import_date: The start date from which to delete transactions (inclusive)
        to_import_date: The end date until which to delete transactions (inclusive, optional)
        
    Returns:
        int: The number of transactions deleted
    """
    from database.models import Transaction
    from sqlalchemy import func
    
    # Build the query filter
    if to_import_date:
        # Delete transactions imported between from_date and to_date (inclusive)
        filter_condition = (
            (Transaction.created_at >= from_import_date) & 
            (Transaction.created_at <= to_import_date)
        )
    else:
        # Delete transactions imported on or after from_date
        filter_condition = (Transaction.created_at >= from_import_date)
    
    # First count how many will be deleted
    count = session.query(func.count(Transaction.transaction_id)).filter(
        filter_condition
    ).scalar()
    
    # Then delete the transactions
    session.query(Transaction).filter(
        filter_condition
    ).delete(synchronize_session=False)
    
    # Commit the changes
    session.commit()
    
    return count
