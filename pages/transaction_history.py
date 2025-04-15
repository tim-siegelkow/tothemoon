import streamlit as st
import pandas as pd
from datetime import datetime

from database.db import get_session, get_all_transactions, update_transaction_category
from utils.csv_handler import export_transactions_to_csv
from config import DEFAULT_CATEGORIES, DATA_DIR

def transaction_history_page():
    st.title("Transaction History")
    
    # Get all transactions
    session = get_session()
    transactions = get_all_transactions(session)
    
    # If no transactions, show message
    if not transactions:
        st.info("No transactions found. Please import data first.")
        return
    
    # Filter options
    st.subheader("Filters")
    
    col1, col2, col3 = st.columns(3)
    
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
            key="history_category"
        )
        st.session_state.filter_category = category_filter
    
    # Show transactions
    st.subheader("Transactions")
    
    # Filter transactions
    filtered_transactions = [
        tx for tx in transactions
        if (tx.date >= st.session_state.filter_start_date and
            tx.date <= st.session_state.filter_end_date and
            (st.session_state.filter_category == "All" or
             tx.category == st.session_state.filter_category))
    ]
    
    # Create dataframe
    if filtered_transactions:
        # Convert to dataframe
        df = pd.DataFrame([
            {
                "id": tx.id,
                "date": tx.date,
                "description": tx.description,
                "amount": tx.amount,
                "category": tx.category
            }
            for tx in filtered_transactions
        ])
        
        # Allow editing of categories
        edited_df = st.data_editor(
            df,
            column_config={
                "id": st.column_config.NumberColumn(
                    "ID",
                    help="Transaction ID",
                    width="small"
                ),
                "date": st.column_config.DateColumn(
                    "Date",
                    help="Transaction date",
                    width="medium",
                    format="YYYY-MM-DD"
                ),
                "description": st.column_config.TextColumn(
                    "Description",
                    help="Transaction description",
                    width="large"
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    help="Transaction amount",
                    width="medium",
                    format="$%.2f"
                ),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Transaction category",
                    width="medium",
                    options=DEFAULT_CATEGORIES
                )
            },
            hide_index=True,
            num_rows="fixed",
            key="history_transactions_df"
        )
        
        # Check for category updates
        if not df.equals(edited_df):
            # Find changed rows
            for index, row in edited_df.iterrows():
                orig_row = df.loc[df["id"] == row["id"]].iloc[0]
                
                # Check if category changed
                if orig_row["category"] != row["category"]:
                    # Update category in database
                    update_transaction_category(session, row["id"], row["category"])
            
            # Commit changes
            session.commit()
            
            # Show success message
            st.success("Transaction categories updated")
        
        # Export button
        if st.button("Export Filtered Data to CSV"):
            export_path = f"transaction_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            if export_transactions_to_csv(filtered_transactions, export_path):
                st.success(f"Data exported to {export_path}")
            else:
                st.error("Error exporting data")
    else:
        st.info("No transactions match the current filters.") 