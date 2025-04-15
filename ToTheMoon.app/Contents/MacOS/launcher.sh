#!/bin/bash

# Open a Terminal window to show the process
osascript -e 'tell app "Terminal"
    do script "cd \"/Users/timsiegelkow/Projects/tothemoon\" && source venv/bin/activate && echo \"Checking dependencies...\" && pip install -r requirements.txt && echo \"Installing Notion client...\" && pip install notion-client && echo \"Starting ToTheMoon...\" && streamlit run streamlit_app.py"
    set custom title of front window to "ToTheMoon Finance"
end tell'
