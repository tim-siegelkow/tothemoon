import os
from datetime import datetime
from notion_client import Client
import pandas as pd
import streamlit as st
from database.models import Transaction

class NotionHandler:
    def __init__(self, token=None, database_id=None):
        """Initialize the Notion handler with API token and database ID."""
        self.token = token
        self.database_id = database_id
        self.client = None
        if token:
            self.client = Client(auth=token)
    
    def connect(self, token):
        """Connect to Notion API with the given token."""
        self.token = token
        self.client = Client(auth=token)
        return self._test_connection()
    
    def _test_connection(self):
        """Test the connection to Notion API."""
        try:
            # Try to retrieve user info to test the connection
            self.client.users.me()
            return True
        except Exception as e:
            print(f"Notion connection error: {e}")
            return False
    
    def set_database_id(self, database_id):
        """Set the Notion database ID."""
        self.database_id = database_id
    
    def push_transactions(self, transactions, progress_callback=None):
        """
        Push transactions to Notion database with detailed error tracking.
        
        Args:
            transactions: List of Transaction objects to push
            progress_callback: Optional callback function to report progress
            
        Returns:
            tuple: (success_status, results_dict)
        """
        if not self.client or not self.database_id:
            return False, "Notion API token or database ID not set"
        
        # Verify database exists and is accessible
        try:
            database = self.client.databases.retrieve(self.database_id)
        except Exception as e:
            return False, f"Failed to access Notion database: {e}"
        
        results = {
            "success": 0, 
            "failed": 0, 
            "skipped": 0,
            "total": len(transactions),
            "errors": []  # Store specific error messages
        }
        
        # Check for existing transactions to avoid duplicates
        try:
            existing_transactions = self._get_existing_transactions()
        except Exception as e:
            existing_transactions = []
            results["errors"].append(f"Failed to fetch existing transactions: {str(e)}")
        
        for idx, transaction in enumerate(transactions):
            try:
                # Create a transaction identifier based on date and description
                transaction_id = f"{transaction.date.strftime('%Y-%m-%d')}_{transaction.description}_{transaction.amount}"
                
                # Skip if already exists in Notion
                if transaction_id in existing_transactions:
                    results["skipped"] += 1
                    if progress_callback:
                        progress_callback(idx + 1, len(transactions), results)
                    continue
                
                # Create a page in the Notion database for the transaction
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties={
                        "Date": {
                            "date": {
                                "start": transaction.date.strftime("%Y-%m-%d")
                            }
                        },
                        "Description": {
                            "title": [
                                {
                                    "text": {
                                        "content": transaction.description
                                    }
                                }
                            ]
                        },
                        "Amount": {
                            "number": transaction.amount
                        },
                        "Category": {
                            "select": {
                                "name": transaction.user_verified_category or transaction.ai_suggested_category or "Uncategorized"
                            }
                        },
                        "Amount Reimbursed": {
                            "number": None
                        }
                    }
                )
                results["success"] += 1
            except Exception as e:
                error_message = f"Failed to push transaction {transaction.transaction_id}: {str(e)}"
                results["failed"] += 1
                results["errors"].append(error_message)
                print(error_message)
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback(idx + 1, len(transactions), results)
        
        return True, results
    
    def _get_existing_transactions(self):
        """
        Fetch existing transactions from Notion to avoid duplicates.
        Returns a set of transaction identifiers.
        """
        existing = set()
        
        try:
            # Query the database
            response = self.client.databases.query(
                database_id=self.database_id,
                page_size=100  # Adjust as needed
            )
            
            # Process results
            for page in response["results"]:
                try:
                    # Extract date, description and amount
                    props = page["properties"]
                    date = props.get("Date", {}).get("date", {}).get("start", "")
                    
                    title_items = props.get("Description", {}).get("title", [])
                    description = title_items[0]["text"]["content"] if title_items else ""
                    
                    amount = props.get("Amount", {}).get("number", 0)
                    
                    # Create unique identifier
                    if date and description:
                        transaction_id = f"{date}_{description}_{amount}"
                        existing.add(transaction_id)
                except Exception:
                    # Skip this entry if we can't parse it
                    continue
                
            return existing
        except Exception as e:
            print(f"Error fetching existing transactions: {e}")
            return set()  # Return empty set on error
    
    def verify_database_structure(self):
        """Verify that the database has the required properties."""
        if not self.client or not self.database_id:
            return False, "Notion API token or database ID not set"
        
        required_properties = {
            "Date": "date",
            "Description": "title",
            "Amount": "number",
            "Category": "select",
            "Amount Reimbursed": "number",
            "€ Amount (abs)": "formula"
        }
        
        try:
            database = self.client.databases.retrieve(self.database_id)
            properties = database["properties"]
            
            missing_properties = []
            for prop_name, prop_type in required_properties.items():
                if prop_name not in properties:
                    missing_properties.append(prop_name)
                elif properties[prop_name]["type"] != prop_type:
                    missing_properties.append(f"{prop_name} (should be {prop_type})")
            
            if missing_properties:
                return False, f"Database is missing required properties: {', '.join(missing_properties)}"
            
            return True, "Database structure is valid"
        except Exception as e:
            return False, f"Failed to verify database structure: {e}" 