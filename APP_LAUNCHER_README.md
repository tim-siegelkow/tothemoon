# ToTheMoon macOS App Launcher

This guide will help you create a clickable macOS application for ToTheMoon that you can use instead of running commands in the terminal.

## Creating the App Bundle

There are two ways to create the app bundle:

### Method 1: Using the create_app.command script (Easiest)

1. In Finder, navigate to your `tothemoon` project folder
2. Double-click the `create_app.command` file
   - If you get a security warning, right-click the file and select "Open" instead
3. A Terminal window will open and create the app bundle for you
4. Once complete, a Finder window will open showing your new `ToTheMoon.app`

### Method 2: Using Python directly

1. Open Terminal
2. Navigate to your `tothemoon` project folder
3. Activate the virtual environment: `source venv/bin/activate`
4. Run the app builder script: `python create_launcher.py`
5. The script will create a `ToTheMoon.app` in your project folder

## Using the App

Once the app bundle is created:

1. Double-click `ToTheMoon.app` to launch the application
   - The first time you run it, you may need to right-click and select "Open" to bypass macOS security
2. The app will open a browser window with the ToTheMoon application

## Moving the App

You can move the `ToTheMoon.app` to your Applications folder if desired:

1. Drag and drop `ToTheMoon.app` to your Applications folder
2. Create a shortcut in your Dock by dragging the app from Applications to the Dock

## Troubleshooting

If the app doesn't open:

1. Make sure you have activated the virtual environment and installed all requirements
2. Check that your `streamlit_app.py` file is working correctly
3. Try running the app through the terminal to see if there are any error messages
4. Recreate the app bundle using the steps above 