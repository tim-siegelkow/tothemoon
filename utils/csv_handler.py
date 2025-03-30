import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
from io import StringIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_CSV_MAPPING
from database.models import Transaction
from database.db import generate_transaction_hash

def validate_csv(file_content, column_mapping=None):
    """
    Validate the CSV file content and structure.
    
    Args:
        file_content: The content of the CSV file
        column_mapping: A dictionary mapping required columns to their names in the CSV
        
    Returns:
        tuple: (is_valid, error_message, dataframe)
    """
    if column_mapping is None:
        column_mapping = DEFAULT_CSV_MAPPING
    
    try:
        # Read CSV into pandas DataFrame
        df = pd.read_csv(StringIO(file_content))
        
        # Check for required columns - only date, description, and amount are strictly required
        required_columns = ["date", "description", "amount"]
        for field in required_columns:
            if field in column_mapping and column_mapping[field] not in df.columns:
                return False, f"Missing required column '{column_mapping[field]}' (mapped to {field})", None
        
        # Check if amount column can be converted to float
        try:
            # Create a temporary copy of the amount column for checking
            amount_column = df[column_mapping["amount"]].copy()
            # Replace any non-numeric characters and try to convert to float
            amount_column = amount_column.astype(str).str.replace('€', '').str.replace(',', '').str.strip()
            amount_column = pd.to_numeric(amount_column, errors='coerce')
            # Check if we have too many NaN values
            nan_count = amount_column.isna().sum()
            if nan_count > 0.5 * len(df):  # If more than 50% of values are NaN
                return False, f"More than half of the values in the amount column could not be converted to numbers", None
        except Exception as e:
            return False, f"Error validating amount column: {str(e)}", None
        
        return True, "", df
    
    except Exception as e:
        return False, f"Error processing CSV: {str(e)}", None

def process_csv(df, column_mapping=None):
    """
    Process the CSV data and convert it to Transaction objects.
    
    Args:
        df: The pandas DataFrame containing transaction data
        column_mapping: A dictionary mapping required columns to their names in the CSV
        
    Returns:
        list: List of Transaction objects
    """
    if column_mapping is None:
        column_mapping = DEFAULT_CSV_MAPPING
    
    transactions = []
    
    for _, row in df.iterrows():
        # Parse date
        date_str = row[column_mapping["date"]]
        try:
            # Try common date formats
            for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    date = datetime.strptime(date_str, date_format)
                    break
                except ValueError:
                    continue
            else:
                # If no format worked, try pandas to_datetime as a fallback
                date = pd.to_datetime(date_str)
        except Exception:
            # Default to current date if parsing fails
            date = datetime.now()
            
        # Get description and amount
        description = str(row[column_mapping["description"]])
        # Handle potential missing data in description field
        if pd.isna(description) or description == "nan":
            # Try to use payment reference as a fallback if it exists
            if "payment_reference" in column_mapping and column_mapping["payment_reference"] in df.columns:
                payment_ref = str(row[column_mapping["payment_reference"]])
                if payment_ref and not pd.isna(payment_ref) and payment_ref != "nan":
                    description = payment_ref
                else:
                    description = "Unknown"
            else:
                description = "Unknown"
        
        # Process amount field
        amount = 0.0
        try:
            amount_str = str(row[column_mapping["amount"]])
            if amount_str and not pd.isna(amount_str) and amount_str != "nan":
                # Remove any currency symbols and commas
                amount_str = amount_str.replace("€", "").replace(",", "").strip()
                amount = float(amount_str)
        except (ValueError, TypeError):
            # If amount cannot be converted to float, try to fallback to original amount
            try:
                if "original_amount" in column_mapping and column_mapping["original_amount"] in df.columns:
                    orig_amount_str = str(row[column_mapping["original_amount"]])
                    if orig_amount_str and not pd.isna(orig_amount_str) and orig_amount_str != "nan":
                        orig_amount_str = orig_amount_str.replace("€", "").replace(",", "").strip()
                        amount = float(orig_amount_str)
            except (ValueError, TypeError):
                amount = 0.0
        
        # Extract additional data
        additional_data = {}
        for field in ["value_date", "partner_iban", "type", "payment_reference", 
                      "account_name", "original_amount", "original_currency", "exchange_rate"]:
            if field in column_mapping and column_mapping[field] in df.columns:
                value = row[column_mapping[field]]
                if not pd.isna(value):
                    additional_data[field] = str(value)
        
        # Determine transaction type from Type field or based on amount
        transaction_type = None
        if "type" in additional_data:
            transaction_type = additional_data["type"]
        else:
            # Positive amount is Income, negative is Expense
            transaction_type = "Income" if amount >= 0 else "Expense"
        
        # Original category can be derived from transaction type
        original_category = transaction_type
        
        # Generate a partner name from the description
        partner_name = description.split('[')[0].strip() if '[' in description else description
        
        # Create Transaction object
        transaction = Transaction(
            date=date,
            description=description,
            amount=amount,
            original_category=original_category
        )
        
        # Generate and set the transaction hash
        transaction.transaction_hash = generate_transaction_hash(date, partner_name, amount)
        
        # Store additional data as a string in the description field
        # Format: "Description [Type: X, Account: Y, Reference: Z]"
        extra_info = []
        for key, value in additional_data.items():
            if key != "type" and value: # Type already included as category
                formatted_key = key.replace('_', ' ').title()
                extra_info.append(f"{formatted_key}: {value}")
        
        if extra_info:
            transaction.description = f"{description} [{', '.join(extra_info)}]"
        
        transactions.append(transaction)
    
    return transactions

def export_transactions_to_csv(transactions, file_path):
    """
    Export transactions to a CSV file.
    
    Args:
        transactions: List of Transaction objects
        file_path: Path to save the CSV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert transactions to DataFrame
        data = []
        for t in transactions:
            category = t.user_verified_category or t.ai_suggested_category or t.original_category
            
            data.append({
                "Date": t.date.strftime("%Y-%m-%d"),
                "Description": t.description,
                "Amount": t.amount,
                "Category": category,
                "AI Suggested": t.ai_suggested_category,
                "Confidence": t.confidence_score,
                "User Verified": t.user_verified_category
            })
        
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        
        return True
    
    except Exception as e:
        print(f"Error exporting to CSV: {str(e)}")
        return False
