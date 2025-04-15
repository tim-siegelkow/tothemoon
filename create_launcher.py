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
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
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
    <string>{app_name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
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

# Change to app directory
cd "{project_dir}"

# Make sure venv exists, or create it
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Set Python path
export PYTHONPATH=$PYTHONPATH:"{project_dir}"

# Run the streamlit app in a way that shows output
echo "Starting ToTheMoon app..."
streamlit run streamlit_app.py

# If the app crashes, keep the terminal window open
if [ $? -ne 0 ]; then
    echo ""
    echo "The app crashed. Press any key to close this window..."
    read -n 1
fi
"""
    
    launcher_path = os.path.join(app_dir, "Contents", "MacOS", "launcher.sh")
    with open(launcher_path, "w") as f:
        f.write(launcher_script)
    
    # Make the launcher script executable
    os.chmod(launcher_path, 0o755)
    
    # Create a Terminal launcher wrapper to ensure visibility
    terminal_launcher = f"""#!/bin/bash
osascript -e 'tell app "Terminal"
    do script "cd \\"{project_dir}\\" && \\"${{PWD}}/{app_name}.app/Contents/MacOS/launcher.sh\\""
    set position of first window to {{100, 100}}
    set custom title of first window to "ToTheMoon Finance"
    set size of first window to {{800, 600}}
end tell'
"""
    
    terminal_launcher_path = os.path.join(app_dir, "Contents", "MacOS", "terminal_launcher.sh")
    with open(terminal_launcher_path, "w") as f:
        f.write(terminal_launcher)
    
    # Make the terminal launcher executable
    os.chmod(terminal_launcher_path, 0o755)
    
    # Update the Info.plist to use the terminal launcher
    with open(os.path.join(app_dir, "Contents", "Info.plist"), "r") as f:
        plist_content = f.read()
    
    # Replace the executable with the terminal launcher
    plist_content = plist_content.replace("<string>launcher.sh</string>", "<string>terminal_launcher.sh</string>")
    
    with open(os.path.join(app_dir, "Contents", "Info.plist"), "w") as f:
        f.write(plist_content)
    
    # Try to create an icon
    try:
        create_better_icon(os.path.join(app_dir, "Contents", "Resources"))
    except Exception as e:
        print(f"Could not create icon: {e}")
        print("The app will use the default icon.")
    
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
        # Create a plain text file with a blue background and rocket emoji
        icon_text = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {
  margin: 0;
  padding: 0;
  width: 1024px;
  height: 1024px;
  background: radial-gradient(circle, #4a90e2, #2171c7);
  display: flex;
  justify-content: center;
  align-items: center;
}
.rocket {
  font-size: 750px;
  color: white;
  text-shadow: 0 10px 20px rgba(0,0,0,0.3);
}
</style>
</head>
<body>
<div class="rocket">🚀</div>
</body>
</html>
"""
        html_path = os.path.join(resources_dir, "rocket.html")
        with open(html_path, "w") as f:
            f.write(icon_text)
        
        # Create a temporary PNG file using qlmanage (built into macOS)
        png_path = os.path.join(resources_dir, "rocket.png")
        subprocess.run(["textutil", "-convert", "rtf", html_path, "-output", html_path + ".rtf"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Convert RTF to PDF
        subprocess.run(["textutil", "-convert", "pdf", html_path + ".rtf", "-output", html_path + ".pdf"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Convert PDF to PNG
        subprocess.run(["sips", "-s", "format", "png", html_path + ".pdf", "--out", png_path], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # If the PNG exists, create an iconset
        if os.path.exists(png_path):
            iconset_dir = os.path.join(resources_dir, "AppIcon.iconset")
            os.makedirs(iconset_dir, exist_ok=True)
            
            # Create different sizes
            for size in [16, 32, 64, 128, 256, 512]:
                icon_path = os.path.join(iconset_dir, f"icon_{size}x{size}.png")
                subprocess.run(["sips", "-z", str(size), str(size), png_path, "--out", icon_path],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Create @2x versions
                if size <= 512:
                    icon_path = os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png")
                    subprocess.run(["sips", "-z", str(size*2), str(size*2), png_path, "--out", icon_path],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Convert iconset to icns
            subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", os.path.join(resources_dir, "AppIcon.icns")],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Clean up
            shutil.rmtree(iconset_dir)
            os.remove(png_path)
            if os.path.exists(html_path):
                os.remove(html_path)
            if os.path.exists(html_path + ".rtf"):
                os.remove(html_path + ".rtf")
            if os.path.exists(html_path + ".pdf"):
                os.remove(html_path + ".pdf")
            
            return True
        
    except Exception as e:
        print(f"Simple icon creation error: {e}")
    
    # If all else fails, try the most basic approach
    try:
        # Create a text file with the rocket emoji
        temp_txt = os.path.join(resources_dir, "temp.txt")
        with open(temp_txt, "w") as f:
            f.write("🚀")
        
        # Convert to png using sips
        temp_png = os.path.join(resources_dir, "temp.png")
        subprocess.run(["sips", "-s", "format", "png", temp_txt, "--out", temp_png], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Convert to icns using iconutil
        temp_iconset = os.path.join(resources_dir, "AppIcon.iconset")
        os.makedirs(temp_iconset, exist_ok=True)
        
        # Copy the png to different sizes in the iconset
        for size in [16, 32, 64, 128, 256, 512, 1024]:
            icon_path = os.path.join(temp_iconset, f"icon_{size}x{size}.png")
            subprocess.run(["sips", "-z", str(size), str(size), temp_png, "--out", icon_path],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Also create the @2x versions
            if size <= 512:
                icon_path = os.path.join(temp_iconset, f"icon_{size}x{size}@2x.png")
                subprocess.run(["sips", "-z", str(size*2), str(size*2), temp_png, "--out", icon_path],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Convert iconset to icns
        subprocess.run(["iconutil", "-c", "icns", temp_iconset, "-o", os.path.join(resources_dir, "AppIcon.icns")],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up temporary files
        shutil.rmtree(temp_iconset)
        os.remove(temp_txt)
        os.remove(temp_png)
        
        return True
    
    except Exception as e:
        print(f"Fallback icon creation error: {e}")
        # If all icon creation methods fail, the app will use the default icon
        return False

def create_better_icon(resources_dir):
    """Create a rocket icon using a better method"""
    # Create a python script that generates an SVG icon
    icon_script = """
import cairo
import math
import os

def create_rocket_icon(output_path, size=512):
    # Create a Cairo surface
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surface)
    
    # Background color (transparent)
    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.paint()
    
    # Center of the icon
    center_x = size / 2
    center_y = size / 2
    
    # Rocket dimensions
    rocket_width = size * 0.3
    rocket_height = size * 0.6
    
    # Rocket body (rounded rectangle)
    ctx.save()
    ctx.translate(center_x, center_y)
    
    # Draw rocket body
    ctx.new_path()
    ctx.move_to(-rocket_width/2, rocket_height/3)
    ctx.line_to(-rocket_width/2, -rocket_height/3)
    ctx.arc(0, -rocket_height/3, rocket_width/2, math.pi, 0)
    ctx.line_to(rocket_width/2, rocket_height/3)
    ctx.arc(0, rocket_height/3, rocket_width/2, 0, math.pi)
    ctx.close_path()
    
    # Red gradient for rocket body
    gradient = cairo.LinearGradient(0, -rocket_height/2, 0, rocket_height/2)
    gradient.add_color_stop_rgba(0, 0.9, 0.2, 0.2, 1.0)  # Red at top
    gradient.add_color_stop_rgba(1, 0.7, 0.1, 0.1, 1.0)  # Darker red at bottom
    ctx.set_source(gradient)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.4, 0.1, 0.1, 1.0)
    ctx.set_line_width(2)
    ctx.stroke()
    
    # Rocket window
    ctx.arc(0, -rocket_height/8, rocket_width/4, 0, 2 * math.pi)
    ctx.set_source_rgba(0.8, 0.9, 1.0, 0.9)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.6, 0.7, 0.8, 1.0)
    ctx.set_line_width(2)
    ctx.stroke()
    
    # Rocket fins
    fin_width = rocket_width * 0.6
    fin_height = rocket_height * 0.25
    
    # Left fin
    ctx.move_to(-rocket_width/2, rocket_height/4)
    ctx.line_to(-rocket_width/2 - fin_width, rocket_height/2)
    ctx.line_to(-rocket_width/2, rocket_height/2)
    ctx.close_path()
    
    # Right fin
    ctx.move_to(rocket_width/2, rocket_height/4)
    ctx.line_to(rocket_width/2 + fin_width, rocket_height/2)
    ctx.line_to(rocket_width/2, rocket_height/2)
    ctx.close_path()
    
    # Fill fins
    ctx.set_source_rgba(0.3, 0.3, 0.6, 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.2, 0.2, 0.4, 1.0)
    ctx.set_line_width(2)
    ctx.stroke()
    
    # Rocket flame
    flame_height = rocket_height * 0.4
    
    # Create flame path
    ctx.move_to(-rocket_width/4, rocket_height/3)
    
    # Wavy flame bottom
    for i in range(5):
        amp = rocket_width/4 * (1 - i/5)
        y = rocket_height/3 + (i/4) * flame_height
        x = amp * math.sin(i * math.pi)
        ctx.line_to(x, y)
    
    ctx.line_to(rocket_width/4, rocket_height/3)
    ctx.close_path()
    
    # Flame gradient
    gradient = cairo.LinearGradient(0, rocket_height/3, 0, rocket_height/3 + flame_height)
    gradient.add_color_stop_rgba(0, 1.0, 0.8, 0.0, 1.0)  # Yellow at top
    gradient.add_color_stop_rgba(0.5, 1.0, 0.4, 0.0, 0.8)  # Orange in middle
    gradient.add_color_stop_rgba(1, 1.0, 0.2, 0.0, 0.5)  # Red at bottom
    ctx.set_source(gradient)
    ctx.fill()
    
    # Restore original transformation
    ctx.restore()
    
    # Save the image
    surface.write_to_png(output_path)

if __name__ == "__main__":
    create_app_bundle() 