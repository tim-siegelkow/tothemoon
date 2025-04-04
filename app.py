import streamlit as st
import pandas as pd
import numpy as np
import os
import io
from datetime import datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go

# Import custom modules
from database.db import init_db, get_session, add_transaction, update_transaction_category, get_all_transactions
from database.models import Transaction, AuditLog
from utils.csv_handler import validate_csv, process_csv, export_transactions_to_csv
from utils.visualization import (
    prepare_data_for_viz, generate_monthly_summary, 
    create_category_pie_chart, create_monthly_trend_chart, create_category_bar_chart
)
from ml.training import train_and_save_model, train_from_labeled_csv
from ml.inference import categorize_transactions, load_model
from config import DEFAULT_CATEGORIES, DEFAULT_CSV_MAPPING, DATA_DIR

# Initialize the application
def init_app():
    # Set page config
    st.set_page_config(
        page_title="ToTheMoon - Personal Finance Tracker",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    init_db()
    
    # Set session state variables
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

# Main navigation
def app_navigation():
    st.sidebar.title("🚀 ToTheMoon")
    st.sidebar.caption("Personal Finance Tracker")
    
    navigation = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Import Data", "Verify Transactions", "Transaction History", "Settings"]
    )
    
    return navigation

# Dashboard page
def dashboard_page():
    st.title("Financial Dashboard")
    
    # Get all transactions
    session = get_session()
    transactions = get_all_transactions(session)
    
    # If no transactions, show message
    if not transactions:
        st.info("No transactions found. Please import data to view the dashboard.")
        return
    
    # Prepare data for visualization
    df = prepare_data_for_viz(transactions)
    
    # Generate summary statistics
    summary = generate_monthly_summary(df)
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Income", f"${summary['total_income']:.2f}")
    
    with col2:
        st.metric("Total Expenses", f"${summary['total_expense']:.2f}")
    
    with col3:
        st.metric("Net Savings", f"${summary['net_savings']:.2f}")
        
    # Add filters
    st.subheader("Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.filter_start_date,
            key="dashboard_start_date"
        )
        st.session_state.filter_start_date = datetime.combine(start_date, datetime.min.time())
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state.filter_end_date,
            key="dashboard_end_date"
        )
        st.session_state.filter_end_date = datetime.combine(end_date, datetime.max.time())
    
    # Filter data
    df_filtered = df[
        (df["date"] >= st.session_state.filter_start_date) &
        (df["date"] <= st.session_state.filter_end_date)
    ]
    
    # If no filtered data, show message
    if df_filtered.empty:
        st.info("No transactions found for the selected date range.")
        return
    
    # Monthly trend chart
    st.subheader("Monthly Income vs Expense Trends")
    monthly_trend_chart = create_monthly_trend_chart(df_filtered)
    st.plotly_chart(monthly_trend_chart, use_container_width=True)
    
    # Category charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Expense Distribution by Category")
        expense_pie_chart = create_category_pie_chart(df_filtered, "Expense")
        st.plotly_chart(expense_pie_chart, use_container_width=True)
    
    with col2:
        st.subheader("Income Distribution by Category")
        income_pie_chart = create_category_pie_chart(df_filtered, "Income")
        st.plotly_chart(income_pie_chart, use_container_width=True)
    
    # Monthly category breakdown
    st.subheader("Monthly Expense Breakdown by Category")
    months_to_show = st.slider("Number of months to display", 1, 12, 3)
    category_bar_chart = create_category_bar_chart(df_filtered, months=months_to_show)
    st.plotly_chart(category_bar_chart, use_container_width=True)
    
    # Export button
    if st.button("Export Filtered Data to CSV"):
        export_path = os.path.join(DATA_DIR, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if export_transactions_to_csv([t for t in transactions if t.date >= st.session_state.filter_start_date and t.date <= st.session_state.filter_end_date], export_path):
            st.success(f"Data exported to {export_path}")
        else:
            st.error("Error exporting data")

# Import data page
def import_data_page():
    st.title("Import Transaction Data")
    
    # CSV upload
    st.subheader("Upload CSV File")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Read file content
        file_content = uploaded_file.getvalue().decode("utf-8")
        
        # Validate CSV
        valid, error_message, df = validate_csv(file_content, st.session_state.column_mapping)
        
        if not valid:
            st.error(error_message)
            return
        
        # Display preview
        st.subheader("CSV Preview")
        st.dataframe(df.head())
        
        # Column mapping
        st.subheader("Column Mapping")
        st.info("Map the columns in your CSV to the required fields.")
        
        # Get all columns from CSV
        csv_columns = df.columns.tolist()
        
        # Dynamic column mapping with tabs for better organization
        tab1, tab2 = st.tabs(["Required Fields", "Additional Fields"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                date_column = st.selectbox(
                    "Date Column",
                    csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["date"]) if st.session_state.column_mapping["date"] in csv_columns else 0
                )
                st.session_state.column_mapping["date"] = date_column
                
                description_column = st.selectbox(
                    "Description Column",
                    csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["description"]) if st.session_state.column_mapping["description"] in csv_columns else 0
                )
                st.session_state.column_mapping["description"] = description_column
            
            with col2:
                amount_column = st.selectbox(
                    "Amount Column",
                    csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["amount"]) if st.session_state.column_mapping["amount"] in csv_columns else 0
                )
                st.session_state.column_mapping["amount"] = amount_column
                
                type_column = st.selectbox(
                    "Transaction Type Column (Optional)",
                    ["None"] + csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["type"]) + 1 if "type" in st.session_state.column_mapping and st.session_state.column_mapping["type"] in csv_columns else 0
                )
                if type_column != "None":
                    st.session_state.column_mapping["type"] = type_column
                elif "type" in st.session_state.column_mapping:
                    del st.session_state.column_mapping["type"]
        
        with tab2:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                value_date_column = st.selectbox(
                    "Value Date Column (Optional)",
                    ["None"] + csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["value_date"]) + 1 if "value_date" in st.session_state.column_mapping and st.session_state.column_mapping["value_date"] in csv_columns else 0
                )
                if value_date_column != "None":
                    st.session_state.column_mapping["value_date"] = value_date_column
                elif "value_date" in st.session_state.column_mapping:
                    del st.session_state.column_mapping["value_date"]
                
                partner_iban_column = st.selectbox(
                    "Partner IBAN Column (Optional)",
                    ["None"] + csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["partner_iban"]) + 1 if "partner_iban" in st.session_state.column_mapping and st.session_state.column_mapping["partner_iban"] in csv_columns else 0
                )
                if partner_iban_column != "None":
                    st.session_state.column_mapping["partner_iban"] = partner_iban_column
                elif "partner_iban" in st.session_state.column_mapping:
                    del st.session_state.column_mapping["partner_iban"]
            
            with col2:
                payment_reference_column = st.selectbox(
                    "Payment Reference Column (Optional)",
                    ["None"] + csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["payment_reference"]) + 1 if "payment_reference" in st.session_state.column_mapping and st.session_state.column_mapping["payment_reference"] in csv_columns else 0
                )
                if payment_reference_column != "None":
                    st.session_state.column_mapping["payment_reference"] = payment_reference_column
                elif "payment_reference" in st.session_state.column_mapping:
                    del st.session_state.column_mapping["payment_reference"]
                
                account_name_column = st.selectbox(
                    "Account Name Column (Optional)",
                    ["None"] + csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["account_name"]) + 1 if "account_name" in st.session_state.column_mapping and st.session_state.column_mapping["account_name"] in csv_columns else 0
                )
                if account_name_column != "None":
                    st.session_state.column_mapping["account_name"] = account_name_column
                elif "account_name" in st.session_state.column_mapping:
                    del st.session_state.column_mapping["account_name"]
            
            with col3:
                original_amount_column = st.selectbox(
                    "Original Amount Column (Optional)",
                    ["None"] + csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["original_amount"]) + 1 if "original_amount" in st.session_state.column_mapping and st.session_state.column_mapping["original_amount"] in csv_columns else 0
                )
                if original_amount_column != "None":
                    st.session_state.column_mapping["original_amount"] = original_amount_column
                elif "original_amount" in st.session_state.column_mapping:
                    del st.session_state.column_mapping["original_amount"]
                
                original_currency_column = st.selectbox(
                    "Original Currency Column (Optional)",
                    ["None"] + csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["original_currency"]) + 1 if "original_currency" in st.session_state.column_mapping and st.session_state.column_mapping["original_currency"] in csv_columns else 0
                )
                if original_currency_column != "None":
                    st.session_state.column_mapping["original_currency"] = original_currency_column
                elif "original_currency" in st.session_state.column_mapping:
                    del st.session_state.column_mapping["original_currency"]
                
                exchange_rate_column = st.selectbox(
                    "Exchange Rate Column (Optional)",
                    ["None"] + csv_columns,
                    index=csv_columns.index(st.session_state.column_mapping["exchange_rate"]) + 1 if "exchange_rate" in st.session_state.column_mapping and st.session_state.column_mapping["exchange_rate"] in csv_columns else 0
                )
                if exchange_rate_column != "None":
                    st.session_state.column_mapping["exchange_rate"] = exchange_rate_column
                elif "exchange_rate" in st.session_state.column_mapping:
                    del st.session_state.column_mapping["exchange_rate"]
        
        # Date format
        st.subheader("Date Format")
        date_format = st.selectbox(
            "Select Date Format",
            ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"],
            index=["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"].index(st.session_state.date_format) if st.session_state.date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"] else 0
        )
        st.session_state.date_format = date_format
        
        # Process button
        if st.button("Process CSV"):
            with st.spinner("Processing transactions..."):
                # Process CSV
                transactions = process_csv(df, st.session_state.column_mapping)
                
                # Categorize transactions
                transactions = categorize_transactions(transactions)
                
                # Store in session state
                st.session_state.uploaded_transactions = transactions
                
                # Save to database
                session = get_session()
                added_count = 0
                skipped_count = 0
                
                for transaction in transactions:
                    result = add_transaction(session, transaction)
                    if result:
                        added_count += 1
                    else:
                        skipped_count += 1
                
                if skipped_count > 0:
                    st.success(f"Successfully processed {added_count} new transactions! ({skipped_count} skipped as duplicates)")
                else:
                    st.success(f"Successfully processed {added_count} transactions!")
                
                st.info("Please navigate to 'Verify Transactions' to review and categorize them.")

# Verify transactions page
def verify_transactions_page():
    st.title("Verify Transactions")
    
    # Get all transactions
    session = get_session()
    transactions = get_all_transactions(session, limit=1000)
    
    # If no transactions, show message
    if not transactions:
        st.info("No transactions found. Please import data first.")
        return
    
    # Add filters
    st.subheader("Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.filter_start_date,
            key="verify_start_date"
        )
        st.session_state.filter_start_date = datetime.combine(start_date, datetime.min.time())
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state.filter_end_date,
            key="verify_end_date"
        )
        st.session_state.filter_end_date = datetime.combine(end_date, datetime.max.time())
    
    with col3:
        category_filter = st.selectbox(
            "Category",
            ["All"] + DEFAULT_CATEGORIES,
            index=DEFAULT_CATEGORIES.index(st.session_state.filter_category) + 1 if st.session_state.filter_category in DEFAULT_CATEGORIES else 0
        )
        st.session_state.filter_category = category_filter if category_filter != "All" else None
    
    # Filter transactions
    filtered_transactions = []
    for t in transactions:
        if t.date >= st.session_state.filter_start_date and t.date <= st.session_state.filter_end_date:
            if st.session_state.filter_category is None or t.ai_suggested_category == st.session_state.filter_category or t.user_verified_category == st.session_state.filter_category:
                filtered_transactions.append(t)
    
    # If no filtered transactions, show message
    if not filtered_transactions:
        st.info("No transactions found matching the filters.")
        return
    
    # Display transactions
    st.subheader(f"Transactions ({len(filtered_transactions)})")
    
    # Create a form for each transaction
    for i, transaction in enumerate(filtered_transactions):
        with st.expander(f"{transaction.date.strftime('%Y-%m-%d')} - {transaction.description} - ${transaction.amount:.2f}"):
            # Transaction details
            st.write(f"**Date:** {transaction.date.strftime('%Y-%m-%d')}")
            st.write(f"**Description:** {transaction.description}")
            st.write(f"**Amount:** ${transaction.amount:.2f}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**AI Suggested Category:** {transaction.ai_suggested_category}")
                st.write(f"**Confidence Score:** {transaction.confidence_score:.2f}")
            
            with col2:
                current_category = transaction.user_verified_category or transaction.ai_suggested_category
                new_category = st.selectbox(
                    "Verify Category",
                    DEFAULT_CATEGORIES,
                    index=DEFAULT_CATEGORIES.index(current_category) if current_category in DEFAULT_CATEGORIES else 0,
                    key=f"category_{transaction.transaction_id}"
                )
                
                if st.button("Update", key=f"update_{transaction.transaction_id}"):
                    # Update transaction category
                    update_transaction_category(session, transaction.transaction_id, new_category)
                    st.success("Category updated!")
                    time.sleep(0.5)  # Short delay to show success message
                    st.experimental_rerun()  # Rerun the app to refresh
    
    # Add retrain model button
    st.subheader("Retrain Model")
    st.write("Retrain the ML model with the verified transaction data.")
    
    if st.button("Retrain Model"):
        with st.spinner("Retraining model..."):
            # Get all transactions with verified categories
            verified_transactions = [t for t in transactions if t.user_verified_category is not None]
            
            if len(verified_transactions) < 10:
                st.error("Not enough verified transactions to train the model. Please verify at least 10 transactions.")
                return
            
            # Train model
            vectorizer, model = train_and_save_model(verified_transactions)
            
            if vectorizer is not None and model is not None:
                st.success("Model successfully retrained!")
            else:
                st.error("Error training model.")

# Transaction history page
def transaction_history_page():
    st.title("Transaction History")
    
    # Get all transactions
    session = get_session()
    transactions = get_all_transactions(session)
    
    # If no transactions, show message
    if not transactions:
        st.info("No transactions found. Please import data first.")
        return
    
    # Add filters
    st.subheader("Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.filter_start_date,
            key="history_start_date"
        )
        st.session_state.filter_start_date = datetime.combine(start_date, datetime.min.time())
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state.filter_end_date,
            key="history_end_date"
        )
        st.session_state.filter_end_date = datetime.combine(end_date, datetime.max.time())
    
    with col3:
        category_filter = st.selectbox(
            "Category",
            ["All"] + DEFAULT_CATEGORIES,
            index=DEFAULT_CATEGORIES.index(st.session_state.filter_category) + 1 if st.session_state.filter_category in DEFAULT_CATEGORIES else 0
        )
        st.session_state.filter_category = category_filter if category_filter != "All" else None
    
    with col4:
        transaction_type_filter = st.selectbox(
            "Transaction Type",
            ["All", "Income", "Expense"],
            index=["All", "Income", "Expense"].index(st.session_state.filter_transaction_type) if st.session_state.filter_transaction_type in ["All", "Income", "Expense"] else 0
        )
        st.session_state.filter_transaction_type = transaction_type_filter
    
    # Filter transactions
    filtered_transactions = []
    for t in transactions:
        if t.date >= st.session_state.filter_start_date and t.date <= st.session_state.filter_end_date:
            if st.session_state.filter_category is None or t.user_verified_category == st.session_state.filter_category or t.ai_suggested_category == st.session_state.filter_category:
                if st.session_state.filter_transaction_type == "All" or (st.session_state.filter_transaction_type == "Income" and t.amount > 0) or (st.session_state.filter_transaction_type == "Expense" and t.amount < 0):
                    filtered_transactions.append(t)
    
    # If no filtered transactions, show message
    if not filtered_transactions:
        st.info("No transactions found matching the filters.")
        return
    
    # Convert to DataFrame for display
    data = []
    for t in filtered_transactions:
        category = t.user_verified_category or t.ai_suggested_category or ""
        
        data.append({
            "Date": t.date.strftime("%Y-%m-%d"),
            "Description": t.description,
            "Amount": f"${t.amount:.2f}",
            "Category": category,
            "Type": "Income" if t.amount > 0 else "Expense"
        })
    
    df = pd.DataFrame(data)
    
    # Display transactions
    st.subheader(f"Transactions ({len(filtered_transactions)})")
    st.dataframe(df, use_container_width=True)
    
    # Export button
    if st.button("Export to CSV"):
        export_path = os.path.join(DATA_DIR, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if export_transactions_to_csv(filtered_transactions, export_path):
            st.success(f"Data exported to {export_path}")
        else:
            st.error("Error exporting data")

# Settings page
def settings_page():
    st.title("Settings")
    
    # CSV mapping settings
    st.subheader("Default CSV Column Mapping")
    st.write("Set the default column names for CSV import.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        date_column = st.text_input("Date Column", st.session_state.column_mapping["date"])
        description_column = st.text_input("Description Column", st.session_state.column_mapping["description"])
    
    with col2:
        amount_column = st.text_input("Amount Column", st.session_state.column_mapping["amount"])
        category_column = st.text_input(
            "Category Column (Optional)",
            st.session_state.column_mapping.get("category", "")
        )
    
    # Update session state
    if st.button("Save Mapping"):
        st.session_state.column_mapping["date"] = date_column
        st.session_state.column_mapping["description"] = description_column
        st.session_state.column_mapping["amount"] = amount_column
        
        if category_column:
            st.session_state.column_mapping["category"] = category_column
        elif "category" in st.session_state.column_mapping:
            del st.session_state.column_mapping["category"]
        
        st.success("Mapping saved!")
    
    # Date format settings
    st.subheader("Default Date Format")
    
    date_format = st.selectbox(
        "Select Date Format",
        ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"],
        index=["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"].index(st.session_state.date_format) if st.session_state.date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"] else 0
    )
    
    if st.button("Save Date Format"):
        st.session_state.date_format = date_format
        st.success("Date format saved!")
    
    # Pre-labeled data upload section
    st.subheader("Initial Model Training")
    st.write("Upload pre-labeled transaction data to train the initial model. The CSV must include a 'Category' column.")
    
    training_csv = st.file_uploader("Upload pre-labeled CSV", type="csv", key="training_csv")
    
    if training_csv is not None:
        # Save the uploaded file temporarily
        temp_path = os.path.join(DATA_DIR, "temp_training_data.csv")
        with open(temp_path, "wb") as f:
            f.write(training_csv.getbuffer())
        
        # Preview the CSV
        st.subheader("CSV Preview")
        try:
            preview_df = pd.read_csv(temp_path)
            st.dataframe(preview_df.head())
            
            # Check if category column exists
            if st.session_state.column_mapping.get("category", "Category") in preview_df.columns:
                # Display category distribution
                if "category" in st.session_state.column_mapping:
                    category_col = st.session_state.column_mapping["category"]
                else:
                    category_col = "Category"
                    
                category_counts = preview_df[category_col].value_counts()
                st.write(f"Found {len(category_counts)} unique categories in {len(preview_df)} transactions")
                
                # Train button
                if st.button("Train Model with Pre-labeled Data"):
                    with st.spinner("Training model..."):
                        vectorizer, model = train_from_labeled_csv(temp_path, st.session_state.column_mapping)
                        
                        if vectorizer is not None and model is not None:
                            st.success("Model trained successfully!")
                        else:
                            st.error("Failed to train model. Check logs for details.")
            else:
                st.error(f"Category column '{st.session_state.column_mapping.get('category', 'Category')}' not found in the CSV.")
                
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")
    
    # Model info
    st.subheader("ML Model Information")
    
    vectorizer, model = load_model()
    
    if vectorizer is not None and model is not None:
        st.write("Model is trained and ready to use.")
        
        # Model details
        st.write(f"Model Type: {type(model).__name__}")
        st.write(f"Number of Features: {vectorizer.get_feature_names_out().shape[0]}")
        st.write(f"Number of Classes: {len(model.classes_)}")
        
        # Display classes
        st.write("Categories in Model:")
        st.write(", ".join(model.classes_))
    else:
        st.warning("Model is not trained yet. Please import data and verify some transactions to train the model.")

# Main function
def main():
    # Initialize app
    init_app()
    
    # Navigation
    navigation = app_navigation()
    
    # Page routing
    if navigation == "Dashboard":
        dashboard_page()
    elif navigation == "Import Data":
        import_data_page()
    elif navigation == "Verify Transactions":
        verify_transactions_page()
    elif navigation == "Transaction History":
        transaction_history_page()
    elif navigation == "Settings":
        settings_page()

if __name__ == "__main__":
    main()
