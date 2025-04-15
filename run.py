#!/usr/bin/env python3
import os
import subprocess
import sys
import argparse
import json

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the script directory to Python path
sys.path.insert(0, script_dir)

# Import after setting path
from config import NOTION_CONFIG_PATH
from utils.notion_handler import NotionHandler
from database.db import init_db, get_session, get_all_transactions

def run_app():
    """Run the Streamlit app."""
    print("Starting ToTheMoon Finance Tracker...")
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Run the Streamlit app
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

def push_to_notion(args):
    """Push data to Notion based on command line arguments."""
    print("Pushing data to Notion...")
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Check if Notion config exists
    if not os.path.exists(NOTION_CONFIG_PATH):
        print("Notion configuration not found. Please configure Notion integration through the web app first.")
        return False
    
    try:
        # Load Notion config
        with open(NOTION_CONFIG_PATH, 'r') as f:
            notion_config = json.load(f)
        
        if not notion_config.get('token') or not notion_config.get('database_id'):
            print("Notion configuration is incomplete. Please configure through the web app.")
            return False
        
        # Initialize Notion handler
        handler = NotionHandler(
            token=notion_config['token'],
            database_id=notion_config['database_id']
        )
        
        # Test connection
        if not handler._test_connection():
            print("Failed to connect to Notion API. Please check your token.")
            return False
        
        # Initialize database
        init_db()
        
        # Get session
        session = get_session()
        
        # Get transactions
        transactions = get_all_transactions(session)
        
        if not transactions:
            print("No transactions found in database.")
            return False
        
        # Filter transactions if needed
        if args.last:
            # Get the most recent transactions
            transactions = sorted(transactions, key=lambda t: t.date, reverse=True)[:args.last]
            print(f"Selected {len(transactions)} most recent transactions.")
        else:
            print(f"Selected all {len(transactions)} transactions.")
        
        # Push to Notion
        print("Pushing transactions to Notion...")
        success, result = handler.push_transactions(transactions)
        
        if success:
            print(f"Successfully pushed {result['success']} transactions to Notion")
            if result['failed'] > 0:
                print(f"{result['failed']} transactions failed to push")
            if result['skipped'] > 0:
                print(f"{result['skipped']} transactions were skipped (already exist)")
            return True
        else:
            print(f"Failed to push transactions: {result}")
            return False
            
    except Exception as e:
        print(f"Error pushing to Notion: {e}")
        return False

def main():
    """Main entry point with command line argument handling."""
    parser = argparse.ArgumentParser(description="ToTheMoon Finance Tracker")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run app command (default)
    run_parser = subparsers.add_parser('run', help='Run the Streamlit web app')
    
    # Notion command
    notion_parser = subparsers.add_parser('notion', help='Push data to Notion')
    notion_parser.add_argument('--last', type=int, help='Push only the last N transactions')
    
    args = parser.parse_args()
    
    # Default to run if no command is provided
    if not args.command or args.command == 'run':
        run_app()
    elif args.command == 'notion':
        push_to_notion(args)

if __name__ == "__main__":
    main() 