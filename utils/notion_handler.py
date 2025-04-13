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
    
    def push_transactions(self, transactions):
        """Push transactions to Notion database."""
        if not self.client or not self.database_id:
            return False, "Notion API token or database ID not set"
        
        # Verify database exists and is accessible
        try:
            database = self.client.databases.retrieve(self.database_id)
        except Exception as e:
            return False, f"Failed to access Notion database: {e}"
        
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        for transaction in transactions:
            try:
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
                print(f"Failed to push transaction {transaction.transaction_id}: {e}")
                results["failed"] += 1
        
        return True, results
    
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