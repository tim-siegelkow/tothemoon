from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import sys
import os
import hashlib
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
    
def get_session():
    """Get a new database session."""
    return Session()

def close_session(session):
    """Close a database session."""
    session.close()
    
def generate_transaction_hash(date, partner_name, amount):
    """Generate a unique hash for a transaction based on date, partner name, and amount."""
    # Convert date to string format
    if isinstance(date, datetime):
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = str(date)
    
    # Create a string combining all values
    combined = f"{date_str}|{partner_name}|{str(amount)}"
    
    # Generate a hash
    return hashlib.md5(combined.encode()).hexdigest()

def transaction_exists(session, transaction_hash):
    """Check if a transaction with the given hash already exists."""
    from database.models import Transaction
    return session.query(Transaction).filter(Transaction.transaction_hash == transaction_hash).first() is not None

def add_transaction(session, transaction):
    """Add a new transaction to the database if it doesn't already exist."""
    # Check if the transaction has a hash, if not generate one
    if not hasattr(transaction, 'transaction_hash') or not transaction.transaction_hash:
        partner_name = transaction.description.split('[')[0].strip() if '[' in transaction.description else transaction.description
        transaction.transaction_hash = generate_transaction_hash(transaction.date, partner_name, transaction.amount)
    
    # Check if transaction already exists
    if transaction_exists(session, transaction.transaction_hash):
        return None  # Transaction already exists
    
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
