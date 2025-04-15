#!/usr/bin/env python3
"""
Simple ToTheMoon App Launcher Creator
Creates a clickable macOS app that launches the ToTheMoon finance app
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def create_app_bundle():
    print("Creating ToTheMoon app launcher...")
    
    # Get the current directory (where tothemoon project is located)
    project_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Create a temporary directory for the app bundle
    app_name = "ToTheMoon"
    app_dir = os.path.join(project_dir, f"{app_name}.app")
    
    # Remove existing app if it exists
    if os.path.exists(app_dir):
        shutil.rmtree(app_dir)
    
    # Create the directory structure
    os.makedirs(os.path.join(app_dir, "Contents", "MacOS"), exist_ok=True)
    os.makedirs(os.path.join(app_dir, "Contents", "Resources"), exist_ok=True)
    
    # Create the Info.plist file
    info_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher.sh</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.tothemoonapp.finance</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>ToTheMoon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
"""
    
    with open(os.path.join(app_dir, "Contents", "Info.plist"), "w") as f:
        f.write(info_plist)
    
    # Create the launcher shell script
    launcher_script = f"""#!/bin/bash

# Open a Terminal window to show the process
osascript -e 'tell app "Terminal"
    do script "cd \\"{project_dir}\\" && source venv/bin/activate && echo \\"Checking dependencies...\\" && pip install -r requirements.txt && echo \\"Installing Notion client...\\" && pip install notion-client && echo \\"Starting ToTheMoon...\\" && streamlit run streamlit_app.py"
    set custom title of front window to "ToTheMoon Finance"
end tell'
"""
    
    launcher_path = os.path.join(app_dir, "Contents", "MacOS", "launcher.sh")
    with open(launcher_path, "w") as f:
        f.write(launcher_script)
    
    # Make the launcher script executable
    os.chmod(launcher_path, 0o755)
    
    # Create a simple rocket icon
    create_simple_icon(os.path.join(app_dir, "Contents", "Resources"))
    
    print(f"\nApplication bundle created at: {app_dir}")
    print("\nTo use:")
    print(f"1. Double-click on {app_name}.app to launch the app")
    print("2. You may need to right-click and select 'Open' the first time")
    print("3. You can move the app to your Applications folder if desired")
    
    # Show in Finder
    subprocess.run(["open", "-R", app_dir])

def create_simple_icon(resources_dir):
    """Create a simple rocket icon using macOS built-in tools"""
    try:
        # Create a simple text file with blue color code and rocket emoji
        html_content = """<!DOCTYPE html>
<html>
<head>
<style>
body {
  background-color: #1e88e5;
  width: 512px;
  height: 512px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
.icon {
  font-size: 300px;
  color: white;
}
</style>
</head>
<body>
<div class="icon">🚀</div>
</body>
</html>"""
        
        html_file = os.path.join(resources_dir, "icon.html")
        with open(html_file, "w") as f:
            f.write(html_content)
        
        # Create a plain text file with just the emoji as fallback
        txt_file = os.path.join(resources_dir, "icon.txt")
        with open(txt_file, "w") as f:
            f.write("🚀")
        
        # Try to use the html file first
        png_file = os.path.join(resources_dir, "rocket.png")
        
        # Try to generate a PNG from the HTML
        try:
            # First convert HTML to PDF
            pdf_file = os.path.join(resources_dir, "icon.pdf")
            subprocess.run(["textutil", "-convert", "pdf", "-output", pdf_file, html_file],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Then convert PDF to PNG
            if os.path.exists(pdf_file):
                subprocess.run(["sips", "-s", "format", "png", pdf_file, "--out", png_file],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.remove(pdf_file)
            else:
                raise Exception("PDF conversion failed")
        except:
            # If HTML method fails, use plain text
            subprocess.run(["sips", "-s", "format", "png", txt_file, "--out", png_file],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Check if PNG was created
        if not os.path.exists(png_file):
            # Create a default png with text
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (512, 512), color=(30, 136, 229))
            d = ImageDraw.Draw(img)
            d.text((200, 200), "🚀", fill=(255, 255, 255), size=200)
            img.save(png_file)
        
        # Convert to icns using iconutil
        iconset_dir = os.path.join(resources_dir, "AppIcon.iconset")
        os.makedirs(iconset_dir, exist_ok=True)
        
        # Create iconset from PNG
        if os.path.exists(png_file):
            # Copy the png to different sizes in the iconset
            for size in [16, 32, 64, 128, 256, 512]:
                icon_path = os.path.join(iconset_dir, f"icon_{size}x{size}.png")
                subprocess.run(["sips", "-z", str(size), str(size), png_file, "--out", icon_path],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Also create the @2x versions
                if size <= 512:
                    icon_path = os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png")
                    subprocess.run(["sips", "-z", str(size*2), str(size*2), png_file, "--out", icon_path],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Convert iconset to icns
            subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", os.path.join(resources_dir, "AppIcon.icns")],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up temporary files
        if os.path.exists(iconset_dir):
            shutil.rmtree(iconset_dir)
        if os.path.exists(txt_file):
            os.remove(txt_file)
        if os.path.exists(html_file):
            os.remove(html_file)
        if os.path.exists(png_file):
            os.remove(png_file)
        
        return True
    
    except Exception as e:
        print(f"Icon creation error: {e}")
        # If icon creation fails, the app will use the default icon
        return False

if __name__ == "__main__":
    create_app_bundle() 