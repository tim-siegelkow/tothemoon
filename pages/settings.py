import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

from database.db import init_db, reset_db, get_session, get_all_transactions
from ml.training import train_and_save_model, train_from_labeled_csv
from config import DEFAULT_CATEGORIES, DATA_DIR

def settings_page():
    st.title("Settings")
    
    # Create tabs for different settings
    tab1, tab2, tab3 = st.tabs(["ML Training", "Database", "Import/Export"])
    
    # ML Training Tab
    with tab1:
        st.header("ML Model Training")
        
        # Train model from database
        st.subheader("Train from Database")
        
        # Get transaction count
        session = get_session()
        transactions = get_all_transactions(session)
        
        if not transactions:
            st.warning("No transactions in database. Please import data first.")
        else:
            st.info(f"Found {len(transactions)} transactions in the database.")
            
            # Training options
            col1, col2 = st.columns(2)
            
            with col1:
                min_samples = st.number_input(
                    "Minimum samples per category",
                    min_value=1,
                    value=5,
                    help="Categories with fewer samples will be excluded"
                )
            
            with col2:
                test_size = st.slider(
                    "Test set size",
                    min_value=0.1,
                    max_value=0.5,
                    value=0.2,
                    step=0.05,
                    help="Portion of data to use for validation"
                )
            
            # Train button
            if st.button("Train Model"):
                try:
                    with st.spinner("Training model..."):
                        # Train the model
                        accuracy, report = train_and_save_model(min_samples, test_size)
                        
                        # Show results
                        st.success(f"Model trained successfully with accuracy: {accuracy:.2f}")
                        
                        # Show classification report
                        st.subheader("Classification Report")
                        st.text(report)
                except Exception as e:
                    st.error(f"Error training model: {str(e)}")
        
        # Train from CSV
        st.subheader("Train from Labeled CSV")
        
        # File uploader
        uploaded_file = st.file_uploader("Upload labeled CSV file", type="csv")
        
        if uploaded_file is not None:
            # Read file
            try:
                df = pd.read_csv(uploaded_file)
                
                # Preview
                st.dataframe(df.head())
                
                # Column selection
                col1, col2 = st.columns(2)
                
                with col1:
                    text_col = st.selectbox(
                        "Description column",
                        df.columns.tolist(),
                        index=df.columns.get_loc("description") if "description" in df.columns else 0
                    )
                
                with col2:
                    label_col = st.selectbox(
                        "Category column",
                        df.columns.tolist(),
                        index=df.columns.get_loc("category") if "category" in df.columns else 0
                    )
                
                # Train button
                if st.button("Train from CSV"):
                    try:
                        with st.spinner("Training model from CSV..."):
                            # Train model
                            accuracy, report = train_from_labeled_csv(df, text_col, label_col)
                            
                            # Show results
                            st.success(f"Model trained successfully with accuracy: {accuracy:.2f}")
                            
                            # Show classification report
                            st.subheader("Classification Report")
                            st.text(report)
                    except Exception as e:
                        st.error(f"Error training model: {str(e)}")
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
    
    # Database Tab
    with tab2:
        st.header("Database Management")
        
        # Reset database section
        st.subheader("Reset Database")
        st.warning("This will delete all data in the database!")
        
        # Create columns for the container
        col1, col2 = st.columns([3, 1])
        
        with col1:
            reset_reason = st.text_input(
                "Reason for reset",
                placeholder="Please explain why you want to reset the database",
                key="reset_reason"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("Reset Database", type="primary", disabled=not reset_reason):
                with st.spinner("Resetting database..."):
                    try:
                        # Reset the database
                        reset_db()
                        st.success("Database reset successfully!")
                    except Exception as e:
                        st.error(f"Error resetting database: {str(e)}")
        
        # Backup and restore section
        st.subheader("Backup and Restore")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Backup Database")
            
            if st.button("Create Backup"):
                with st.spinner("Creating backup..."):
                    try:
                        # Get all transactions
                        transactions = get_all_transactions(session)
                        
                        if not transactions:
                            st.warning("No transactions to backup")
                        else:
                            # Convert to JSON
                            backup_data = []
                            for tx in transactions:
                                backup_data.append({
                                    "id": tx.id,
                                    "date": tx.date.isoformat(),
                                    "description": tx.description,
                                    "amount": tx.amount,
                                    "category": tx.category,
                                    "transaction_type": tx.transaction_type,
                                    "account_name": tx.account_name
                                })
                            
                            # Save to file
                            backup_path = os.path.join(DATA_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                            with open(backup_path, "w") as f:
                                json.dump(backup_data, f, indent=2)
                            
                            st.success(f"Backup created: {backup_path}")
                    except Exception as e:
                        st.error(f"Error creating backup: {str(e)}")
        
        with col2:
            st.write("Restore from Backup")
            
            # File uploader
            backup_file = st.file_uploader("Upload backup file", type="json")
            
            if backup_file is not None:
                try:
                    # Load JSON
                    backup_data = json.load(backup_file)
                    
                    st.info(f"Found {len(backup_data)} transactions in backup")
                    
                    # Restore button
                    if st.button("Restore from Backup"):
                        with st.spinner("Restoring from backup..."):
                            try:
                                # Reset database first
                                reset_db()
                                
                                # Get session
                                session = get_session()
                                
                                # Add each transaction
                                for tx_data in backup_data:
                                    # Convert date back to datetime
                                    tx_data["date"] = datetime.fromisoformat(tx_data["date"])
                                    
                                    # Create transaction
                                    from database.models import Transaction
                                    tx = Transaction(**tx_data)
                                    session.add(tx)
                                
                                # Commit
                                session.commit()
                                
                                st.success(f"Successfully restored {len(backup_data)} transactions")
                            except Exception as e:
                                st.error(f"Error restoring from backup: {str(e)}")
                except Exception as e:
                    st.error(f"Error reading backup file: {str(e)}")
    
    # Import/Export Tab
    with tab3:
        st.header("Import/Export Settings")
        
        # Transaction deletion
        st.subheader("Delete Transactions by Date")
        
        if "tx_date_selection" not in st.session_state:
            st.session_state.tx_date_selection = None
        if "tx_confirm_delete" not in st.session_state:
            st.session_state.tx_confirm_delete = False
        
        # Date selection
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            tx_start_date = st.date_input(
                "Start Date",
                value=datetime.now().replace(day=1),
                key="tx_start_date"
            )
        
        with col2:
            tx_end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                key="tx_end_date"
            )
        
        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            preview_button = st.button("Preview Transactions", key="preview_tx_date")
        
        if preview_button:
            preview_tx_date_click()
        
        # Display selected transactions
        if st.session_state.tx_date_selection is not None:
            # Show transaction count
            tx_count = len(st.session_state.tx_date_selection)
            
            if tx_count > 0:
                st.info(f"Found {tx_count} transactions to delete")
                
                # Show data sample
                st.dataframe(pd.DataFrame([
                    {
                        "date": tx.date.strftime("%Y-%m-%d"),
                        "description": tx.description,
                        "amount": tx.amount,
                        "category": tx.category
                    }
                    for tx in st.session_state.tx_date_selection[:10]
                ]))
                
                if tx_count > 10:
                    st.caption(f"Showing 10 of {tx_count} transactions")
                
                # Delete button
                if not st.session_state.tx_confirm_delete:
                    if st.button("Delete These Transactions", key="confirm_tx_delete"):
                        confirm_tx_delete_click()
                else:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Yes, Delete Transactions", type="primary", key="execute_tx_delete"):
                            execute_tx_delete()
                    
                    with col2:
                        if st.button("Cancel", key="cancel_tx_delete"):
                            reset_tx_deletion()
            else:
                st.info("No transactions found in the selected date range")
                st.session_state.tx_date_selection = None
        
        # Clear data older than X months
        st.subheader("Delete Old Import Data")
        
        if "import_date_selection" not in st.session_state:
            st.session_state.import_date_selection = None
        if "import_confirm_delete" not in st.session_state:
            st.session_state.import_confirm_delete = False
        
        # Months selection
        col1, col2 = st.columns([3, 1])
        
        with col1:
            months = st.slider(
                "Delete data older than X months",
                min_value=1,
                max_value=60,
                value=12,
                step=1,
                key="import_months"
            )
        
        with col2:
            st.write("")  # Spacing
            preview_button = st.button("Preview Data", key="preview_import_date")
        
        if preview_button:
            preview_import_date_click()
        
        # Display selected import data
        if st.session_state.import_date_selection is not None:
            # Show data count
            data_count = len(st.session_state.import_date_selection)
            
            if data_count > 0:
                st.info(f"Found {data_count} data files to delete")
                
                # Show data sample
                st.dataframe(pd.DataFrame([
                    {
                        "filename": os.path.basename(file_path),
                        "path": file_path,
                        "size": f"{os.path.getsize(file_path) / 1024:.1f} KB",
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    for file_path in st.session_state.import_date_selection[:10]
                ]))
                
                if data_count > 10:
                    st.caption(f"Showing 10 of {data_count} files")
                
                # Delete button
                if not st.session_state.import_confirm_delete:
                    if st.button("Delete These Files", key="confirm_import_delete"):
                        confirm_import_delete_click()
                else:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Yes, Delete Files", type="primary", key="execute_import_delete"):
                            execute_import_delete()
                    
                    with col2:
                        if st.button("Cancel", key="cancel_import_delete"):
                            reset_import_deletion()
            else:
                st.info("No old data files found")
                st.session_state.import_date_selection = None

# Helper functions for transaction deletion
def preview_tx_date_click():
    # Get the date range
    start_date = datetime.combine(st.session_state.tx_start_date, datetime.min.time())
    end_date = datetime.combine(st.session_state.tx_end_date, datetime.max.time())
    
    # Get transactions
    session = get_session()
    transactions = get_all_transactions(session)
    
    # Filter transactions
    filtered_transactions = [
        tx for tx in transactions
        if start_date <= tx.date <= end_date
    ]
    
    # Store in session state
    st.session_state.tx_date_selection = filtered_transactions
    
    # Reset confirmation
    st.session_state.tx_confirm_delete = False

def confirm_tx_delete_click():
    st.session_state.tx_confirm_delete = True

def execute_tx_delete():
    # Get session
    session = get_session()
    
    # Delete transactions
    try:
        for tx in st.session_state.tx_date_selection:
            session.delete(tx)
        
        # Commit
        session.commit()
        
        # Show success message
        st.success(f"Successfully deleted {len(st.session_state.tx_date_selection)} transactions")
        
        # Reset state
        reset_tx_deletion()
    except Exception as e:
        st.error(f"Error deleting transactions: {str(e)}")

def reset_tx_deletion():
    st.session_state.tx_date_selection = None
    st.session_state.tx_confirm_delete = False

# Helper functions for import data deletion
def preview_import_date_click():
    # Get months
    months = st.session_state.import_months
    
    # Calculate cutoff date
    cutoff_date = datetime.now().replace(day=1) - pd.DateOffset(months=months)
    
    # Get all files in data directory
    data_files = []
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".csv") or file.endswith(".json"):
                file_path = os.path.join(root, file)
                
                # Get modification time
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Check if older than cutoff
                if mod_time < cutoff_date:
                    data_files.append(file_path)
    
    # Store in session state
    st.session_state.import_date_selection = data_files
    
    # Reset confirmation
    st.session_state.import_confirm_delete = False

def confirm_import_delete_click():
    st.session_state.import_confirm_delete = True

def execute_import_delete():
    # Delete files
    try:
        deleted_count = 0
        for file_path in st.session_state.import_date_selection:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception:
                pass
        
        # Show success message
        st.success(f"Successfully deleted {deleted_count} files")
        
        # Reset state
        reset_import_deletion()
    except Exception as e:
        st.error(f"Error deleting files: {str(e)}")

def reset_import_deletion():
    st.session_state.import_date_selection = None
    st.session_state.import_confirm_delete = False 