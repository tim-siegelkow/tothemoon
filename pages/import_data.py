import streamlit as st
import pandas as pd
import os
import io
import json
import time
from datetime import datetime

from database.db import get_session, add_transaction
from utils.csv_handler import validate_csv, process_csv
from ml.inference import categorize_transactions, load_model
from config import DEFAULT_CATEGORIES, DEFAULT_CSV_MAPPING

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
            st.error(f"Invalid CSV format: {error_message}")
        else:
            # Show preview of the data
            st.subheader("Data Preview")
            st.dataframe(df.head(5))
            
            # Mapping configuration
            st.subheader("Column Mapping")
            
            # Create two columns for the mapping fields
            col1, col2 = st.columns(2)
            
            # Show current mapping and allow updates
            with col1:
                st.session_state.column_mapping["date"] = st.text_input(
                    "Date Column",
                    value=st.session_state.column_mapping["date"],
                    key="date_col"
                )
                
                st.session_state.column_mapping["description"] = st.text_input(
                    "Description Column",
                    value=st.session_state.column_mapping["description"],
                    key="desc_col"
                )
                
                st.session_state.column_mapping["amount"] = st.text_input(
                    "Amount Column",
                    value=st.session_state.column_mapping["amount"],
                    key="amount_col"
                )
                
                date_format = st.text_input(
                    "Date Format (e.g., %Y-%m-%d)",
                    value=st.session_state.date_format,
                    key="date_format_input"
                )
                st.session_state.date_format = date_format
            
            with col2:
                st.session_state.column_mapping["type"] = st.text_input(
                    "Transaction Type Column (optional)",
                    value=st.session_state.column_mapping.get("type", ""),
                    key="type_col"
                )
                
                st.session_state.column_mapping["category"] = st.text_input(
                    "Category Column (optional)",
                    value=st.session_state.column_mapping.get("category", ""),
                    key="category_col"
                )
                
                st.session_state.column_mapping["account_name"] = st.text_input(
                    "Account Name Column (optional)",
                    value=st.session_state.column_mapping.get("account_name", ""),
                    key="account_col"
                )
            
            # Process data button
            if st.button("Process Data"):
                try:
                    with st.spinner("Processing data..."):
                        # Process the CSV data
                        transactions, error_rows = process_csv(
                            file_content,
                            st.session_state.column_mapping,
                            st.session_state.date_format
                        )
                        
                        if transactions:
                            # Store transactions in session state
                            st.session_state.uploaded_transactions = transactions
                            
                            # Try to categorize transactions using ML
                            try:
                                # Load the ML model
                                model, vectorizer = load_model()
                                
                                if model and vectorizer:
                                    # Update the progress bar
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    # Define a callback for the categorization process
                                    def update_progress(current, total, results):
                                        # Update progress bar
                                        progress = int((current / total) * 100)
                                        progress_bar.progress(progress)
                                        status_text.text(f"Categorizing transactions: {current}/{total}")
                                    
                                    # Categorize the transactions
                                    categorize_transactions(
                                        st.session_state.uploaded_transactions,
                                        model,
                                        vectorizer,
                                        update_progress
                                    )
                                    
                                    # Clear the progress indicators
                                    time.sleep(0.5)
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    st.success(f"Successfully processed {len(transactions)} transactions with AI categorization")
                                else:
                                    st.warning("No ML model found. Transactions will need manual categorization.")
                                    st.success(f"Successfully processed {len(transactions)} transactions")
                            except Exception as e:
                                st.warning(f"Error during AI categorization: {str(e)}")
                                st.success(f"Successfully processed {len(transactions)} transactions (without AI categorization)")
                            
                            # Show transaction count by category
                            st.subheader("Transaction Categories")
                            
                            # Count transactions by category
                            category_counts = {}
                            for tx in st.session_state.uploaded_transactions:
                                category = tx.get("category", "Uncategorized")
                                if category not in category_counts:
                                    category_counts[category] = 0
                                category_counts[category] += 1
                            
                            # Display as a horizontal bar chart
                            chart_data = pd.DataFrame({
                                "Category": list(category_counts.keys()),
                                "Count": list(category_counts.values())
                            })
                            
                            if not chart_data.empty:
                                st.bar_chart(
                                    chart_data.set_index("Category")
                                )
                            
                            # Navigate to verification page
                            st.info("Go to the 'Verify Transactions' page to review and save the transactions")
                            
                            if error_rows:
                                st.warning(f"{len(error_rows)} rows had errors and were skipped")
                                with st.expander("Show error rows"):
                                    st.dataframe(pd.DataFrame(error_rows))
                        else:
                            st.error("No valid transactions found in the file")
                            
                            if error_rows:
                                st.warning(f"{len(error_rows)} rows had errors")
                                with st.expander("Show error rows"):
                                    st.dataframe(pd.DataFrame(error_rows))
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
    
    # Save mapping button
    st.subheader("Save Configuration")
    
    if st.button("Save Current Mapping"):
        # Convert mapping to JSON
        mapping_json = json.dumps(st.session_state.column_mapping, indent=2)
        
        # Create a download button
        st.download_button(
            label="Download Mapping Configuration",
            data=mapping_json,
            file_name=f"mapping_config_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    # Load mapping section
    st.subheader("Load Configuration")
    
    uploaded_config = st.file_uploader("Upload Configuration File", type="json")
    
    if uploaded_config is not None:
        try:
            # Load JSON from uploaded file
            mapping_config = json.load(uploaded_config)
            
            # Update session state
            st.session_state.column_mapping = mapping_config
            
            st.success("Configuration loaded successfully")
        except Exception as e:
            st.error(f"Error loading configuration: {str(e)}") 