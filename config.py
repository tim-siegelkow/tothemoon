import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Database
DATABASE_PATH = os.path.join(BASE_DIR, "data", "finance_tracker.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ML model
MODEL_DIR = os.path.join(BASE_DIR, "data", "model")
MODEL_PATH = os.path.join(MODEL_DIR, "transaction_classifier.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")

# Data directories
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure directories exist
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Transaction categories
DEFAULT_CATEGORIES = [
    "Income",
    "Reimbursements",
    "Housing & Utilities",
    "Groceries",
    "Dining",
    "Entertainment",
    "Transportation",
    "Nightlife",
    "Clothing",
    "Home Improvement",
    "Cash Withdrawals",
    "Flights",
    "Accommodation",
    "Health & Fitness",
    "Miscellaneous"
]

# Confidence threshold for auto-categorization
CONFIDENCE_THRESHOLD = 0.7

# CSV column mapping (default values, user can override)
DEFAULT_CSV_MAPPING = {
    "date": "Booking Date",
    "value_date": "Value Date",
    "description": "Partner Name",
    "partner_iban": "Partner Iban",
    "type": "Type",
    "payment_reference": "Payment Reference",
    "account_name": "Account Name",
    "amount": "Amount (EUR)",
    "original_amount": "Original Amount",
    "original_currency": "Original Currency",
    "exchange_rate": "Exchange Rate",
    "category": "Category"
}
