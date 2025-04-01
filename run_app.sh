#!/bin/bash
# Activate virtual environment
source venv/bin/activate

# Add current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run the streamlit app
streamlit run streamlit_app.py 