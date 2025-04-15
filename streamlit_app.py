import os
import sys
from datetime import datetime, timedelta

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add script directory to Python path
sys.path.insert(0, script_dir)

import streamlit as st
from config import DEFAULT_CSV_MAPPING
from database.db import init_db

# Import pages
from pages import (
    dashboard_page,
    import_data_page,
    verify_transactions_page,
    transaction_history_page,
    settings_page,
    notion_integration_page
)

# Initialize the app
def init_app():
    # Set page config
    st.set_page_config(
        page_title="ToTheMoon - Personal Finance Tracker",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state variables
    if "uploaded_transactions" not in st.session_state:
        st.session_state.uploaded_transactions = []
    if "column_mapping" not in st.session_state:
        st.session_state.column_mapping = DEFAULT_CSV_MAPPING.copy()
    if "date_format" not in st.session_state:
        st.session_state.date_format = "%Y-%m-%d"
    if "filter_start_date" not in st.session_state:
        st.session_state.filter_start_date = datetime.now() - timedelta(days=365)
    if "filter_end_date" not in st.session_state:
        st.session_state.filter_end_date = datetime.now()
    if "filter_category" not in st.session_state:
        st.session_state.filter_category = "All"
    if "filter_transaction_type" not in st.session_state:
        st.session_state.filter_transaction_type = "All"

# Navigation
def app_navigation():
    st.sidebar.title("🚀 ToTheMoon")
    st.sidebar.caption("Personal Finance Tracker")
    
    navigation = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Import Data", "Verify Transactions", "Transaction History", "Settings", "Notion Integration"]
    )
    
    return navigation

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
elif nav == "Notion Integration":
    notion_integration_page()
# Add other navigation options as needed 