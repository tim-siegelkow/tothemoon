import os
import sys

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add script directory to Python path
sys.path.insert(0, script_dir)

# Import and run the main app
from app import init_app, app_navigation, dashboard_page, import_data_page, verify_transactions_page, transaction_history_page, settings_page
import streamlit as st

# Initialize the app
init_app()

# Run navigation
nav = app_navigation()

# Display selected page
if nav == "Dashboard":
    dashboard_page()
elif nav == "Import Data":
    import_data_page()
elif nav == "Verify Transactions":
    verify_transactions_page()
elif nav == "Transaction History":
    transaction_history_page()
elif nav == "Settings":
    settings_page()
# Add other navigation options as needed 