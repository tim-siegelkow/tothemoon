import streamlit as st
import os
import json
import time
from datetime import datetime

from database.db import get_session, get_all_transactions
from utils.notion_handler import NotionHandler
from config import NOTION_CONFIG_PATH

def notion_integration_page():
    st.title("Notion Integration")
    
    # Check if config file exists
    notion_config = {}
    if os.path.exists(NOTION_CONFIG_PATH):
        try:
            with open(NOTION_CONFIG_PATH, 'r') as f:
                notion_config = json.load(f)
        except Exception as e:
            st.error(f"Error loading Notion config: {str(e)}")
    
    # Configuration tab
    st.subheader("Configuration")
    
    # API Key input
    api_key = st.text_input(
        "Notion API Key",
        value=notion_config.get("token", ""),
        type="password",
        help="Get your API key from https://www.notion.so/my-integrations"
    )
    
    # Database ID input
    database_id = st.text_input(
        "Notion Database ID",
        value=notion_config.get("database_id", ""),
        help="The ID of your Notion database (from the URL or share link)"
    )
    
    # Save config button
    if st.button("Save Configuration"):
        try:
            # Create config object
            new_config = {
                "token": api_key,
                "database_id": database_id
            }
            
            # Save to file
            os.makedirs(os.path.dirname(NOTION_CONFIG_PATH), exist_ok=True)
            with open(NOTION_CONFIG_PATH, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            # Update local variable
            notion_config = new_config
            
            st.success("Configuration saved successfully")
        except Exception as e:
            st.error(f"Error saving configuration: {str(e)}")
    
    # Test connection
    if api_key and database_id:
        if st.button("Test Connection"):
            with st.spinner("Testing connection to Notion..."):
                try:
                    # Initialize Notion handler
                    handler = NotionHandler(token=api_key, database_id=database_id)
                    
                    # Test connection
                    if handler._test_connection():
                        st.success("Successfully connected to Notion!")
                        
                        # Try to get database schema
                        database_info = handler._get_database_schema()
                        
                        if database_info:
                            st.info("Database properties found:")
                            
                            # Show database properties
                            property_list = []
                            for prop_name, prop_data in database_info.get("properties", {}).items():
                                property_list.append({
                                    "Name": prop_name,
                                    "Type": prop_data.get("type", "Unknown")
                                })
                            
                            if property_list:
                                st.table(property_list)
                        else:
                            st.warning("Could not retrieve database schema")
                    else:
                        st.error("Failed to connect to Notion")
                except Exception as e:
                    st.error(f"Error connecting to Notion: {str(e)}")
    
    # Push data tab
    st.subheader("Push Data to Notion")
    
    if not (api_key and database_id):
        st.warning("Please configure your Notion API key and database ID first")
    else:
        # Get transactions
        session = get_session()
        transactions = get_all_transactions(session)
        
        if not transactions:
            st.info("No transactions found in the database")
        else:
            st.info(f"Found {len(transactions)} transactions in the database")
            
            # Filter options
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=st.session_state.filter_start_date,
                    key="notion_start_date"
                )
                st.session_state.filter_start_date = datetime.combine(start_date, datetime.min.time())
            
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=st.session_state.filter_end_date,
                    key="notion_end_date"
                )
                st.session_state.filter_end_date = datetime.combine(end_date, datetime.max.time())
            
            # Filter transactions
            filtered_transactions = [
                tx for tx in transactions
                if (tx.date >= st.session_state.filter_start_date and
                    tx.date <= st.session_state.filter_end_date)
            ]
            
            st.info(f"{len(filtered_transactions)} transactions match the date filter")
            
            # Push button
            if st.button("Push Transactions to Notion"):
                if filtered_transactions:
                    with st.spinner("Pushing data to Notion..."):
                        try:
                            # Initialize Notion handler
                            handler = NotionHandler(token=api_key, database_id=database_id)
                            
                            # Show progress
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # Define progress callback
                            def update_progress(current, total, results):
                                # Update progress bar
                                progress = int((current / total) * 100)
                                progress_bar.progress(progress)
                                
                                # Update status text
                                success_count = results.get("success", 0)
                                failed_count = results.get("failed", 0)
                                skipped_count = results.get("skipped", 0)
                                
                                status_text.text(f"Processing: {current}/{total} - "
                                               f"Success: {success_count}, "
                                               f"Failed: {failed_count}, "
                                               f"Skipped: {skipped_count}")
                            
                            # Push transactions
                            success, results = handler.push_transactions(filtered_transactions, update_progress)
                            
                            # Clear progress bar after a short delay
                            time.sleep(0.5)
                            progress_bar.empty()
                            
                            if success:
                                st.success(f"Successfully pushed {results['success']} transactions to Notion")
                                
                                if results["failed"] > 0:
                                    st.warning(f"{results['failed']} transactions failed to push")
                                
                                if results["skipped"] > 0:
                                    st.info(f"{results['skipped']} transactions were skipped (already exist in Notion)")
                            else:
                                st.error("Failed to push transactions to Notion")
                        except Exception as e:
                            st.error(f"Error pushing to Notion: {str(e)}")
                else:
                    st.warning("No transactions match the current filters")
    
    # Help info
    with st.expander("How to set up Notion integration"):
        st.markdown("""
        ## Setting up Notion Integration
        
        1. **Create a Notion integration**:
           - Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
           - Click "New integration"
           - Give it a name (e.g., "ToTheMoon Finance")
           - Select the capabilities: Read content, Update content, Insert content
           - Copy the "Internal Integration Token" (this is your API key)
        
        2. **Create a database in Notion**:
           - Create a new page in Notion
           - Add a database (full page or inline)
           - Make sure it has the following properties:
             - Date (date type)
             - Description (text type)
             - Amount (number type)
             - Category (select type)
        
        3. **Share the database with your integration**:
           - Open your database in Notion
           - Click the "Share" button
           - In the "Invite" field, find and select your integration
           - Click "Invite"
        
        4. **Get the database ID**:
           - Open your database in Notion
           - Look at the URL, it will look like: `https://www.notion.so/workspace/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX?v=...`
           - Copy the part after the last slash and before the question mark (XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)
        
        5. **Enter the API key and database ID in this page**
        
        6. **Click "Test Connection" to verify it works**
        """)

    # Documentation
    with st.expander("Data synchronization details"):
        st.markdown("""
        ## How data synchronization works
        
        When you push data to Notion:
        
        1. Each transaction is converted to a Notion database entry
        2. Transactions are matched by date, description, and amount to avoid duplicates
        3. If a transaction already exists, it will be skipped
        4. Notion pages will include:
           - Date property (the transaction date)
           - Name (the transaction description)
           - Amount property (the transaction amount)
           - Category property (the transaction category)
        
        Note that synchronization is one-way (from this app to Notion).
        Changes made in Notion will not be reflected back in this app.
        """) 