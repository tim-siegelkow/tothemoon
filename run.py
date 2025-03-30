#!/usr/bin/env python3
import os
import subprocess
import sys

def run_app():
    """Run the Streamlit app."""
    print("Starting ToTheMoon Finance Tracker...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Run the Streamlit app
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

if __name__ == "__main__":
    run_app() 