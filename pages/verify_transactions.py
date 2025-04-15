import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

from database.db import get_session, add_transaction
from config import DEFAULT_CATEGORIES

def verify_transactions_page():
    st.title("Verify Transactions")
    
    # Check if there are uploaded transactions
    if not st.session_state.uploaded_transactions:
        st.info("No transactions to verify. Please import data first.")
        return
    
    # Show the number of transactions
    st.subheader(f"{len(st.session_state.uploaded_transactions)} Transactions to Verify")
    
    # Create a form for verification
    with st.form("verify_transactions_form"):
        # Create a dataframe from the transactions
        transactions_df = pd.DataFrame(st.session_state.uploaded_transactions)
        
        # Create selection columns
        transactions_df["verified"] = True
        
        # If category is not present in some transactions, add it
        if "category" not in transactions_df.columns:
            transactions_df["category"] = "Uncategorized"
        
        # Check if confidence scores are available
        has_confidence = "confidence" in transactions_df.columns
        
        # Display the transactions
        edited_df = st.data_editor(
            transactions_df[[
                "date", "description", "amount", "category", 
                "verified", **({"confidence": np.round} if has_confidence else {})
            ]],
            column_config={
                "date": st.column_config.DateColumn(
                    "Date",
                    help="Transaction date",
                    width="medium",
                    format="YYYY-MM-DD",
                ),
                "description": st.column_config.TextColumn(
                    "Description",
                    help="Transaction description",
                    width="large",
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    help="Transaction amount",
                    width="medium",
                    format="$%.2f",
                ),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Transaction category",
                    width="medium",
                    options=DEFAULT_CATEGORIES,
                ),
                "verified": st.column_config.CheckboxColumn(
                    "Import",
                    help="Check to import this transaction",
                    width="small",
                ),
                **({"confidence": st.column_config.ProgressColumn(
                    "Confidence",
                    help="AI confidence in category",
                    width="small",
                    format="%f",
                    min_value=0,
                    max_value=1,
                )} if has_confidence else {})
            },
            hide_index=True,
            num_rows="dynamic",
            key="verify_transactions_df"
        )
        
        # Submit button
        submitted = st.form_submit_button("Save Verified Transactions")
        
        if submitted:
            # Filter verified transactions
            verified_transactions = edited_df[edited_df["verified"]]
            
            if verified_transactions.empty:
                st.error("No transactions selected for import")
                return
            
            # Save to database
            with st.spinner("Saving transactions..."):
                # Get database session
                session = get_session()
                
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Save each transaction
                saved_count = 0
                total_count = len(verified_transactions)
                
                for index, tx in verified_transactions.iterrows():
                    # Convert to dictionary for easier handling
                    tx_dict = tx.to_dict()
                    
                    # Add transaction
                    add_transaction(session, tx_dict)
                    
                    # Update progress
                    saved_count += 1
                    progress = int((saved_count / total_count) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Saving transactions: {saved_count}/{total_count}")
                    
                    # Short delay to show progress
                    time.sleep(0.01)
                
                # Commit session
                session.commit()
                
                # Clear progress bar after a short delay
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                # Show success message
                st.success(f"Successfully saved {saved_count} transactions")
                
                # Clear the uploaded transactions
                st.session_state.uploaded_transactions = [] 