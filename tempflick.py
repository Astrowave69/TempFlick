import ctypes
import sys
import os
import shutil
import time
import threading
import tkinter as tk
from tkinter import messagebox
from plyer import notification
import json
import winreg as reg

# Function to check if the script is running as administrator
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# Function to restart the script as an administrator
def run_as_admin():
    # Get the full path of the current script
    script_path = sys.argv[0]
    # Run the script as administrator using the shell
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)

# If not running as admin, restart the script with admin privileges
if not is_admin():
    run_as_admin()
    sys.exit()

# Function to clean temp directories
def clean_temp_dirs():
    # Directories to clean
    temp_dirs = [r"C:\Windows\Prefetch", os.getenv('TEMP'), os.getenv('TMP'), r"C:\Windows\Temp"]
    cleaned_dirs = []

    for path in temp_dirs:
        try:
            # Check if the directory exists
            if os.path.exists(path):
                print(f"Cleaning directory: {path}")  # Debugging line
                for file_name in os.listdir(path):
                    file_path = os.path.join(path, file_name)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)  # Delete the file
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)  # Delete the folder
                    except Exception as e:
                        # Skip files that can't be deleted (in use or protected)
                        print(f"Could not delete {file_path}: {e}")  # Debugging line
                        continue
                cleaned_dirs.append(path)
            else:
                print(f"Directory {path} not found.")  # Debugging line
        except Exception as e:
            # Handle any errors when accessing the folder
            print(f"Error accessing {path}: {e}")  # Debugging line
    
    if cleaned_dirs:
        notification.notify(
            title="TempFlick - Cleanup Complete",
            message="All temporary files have been cleaned successfully.",
            timeout=10
        )

# Function to load settings from config file
def load_settings():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as config_file:
            return json.load(config_file)
    return {"run_on_startup": False}

# Function to save settings to config file
def save_settings(settings):
    with open('config.json', 'w') as config_file:
        json.dump(settings, config_file)

# Function to toggle the app's startup setting
def toggle_startup(run_on_startup):
    # Path to the registry key for startup programs
    key = reg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "TempFlick"
    app_path = sys.executable

    # Open the registry key
    reg_key = reg.OpenKey(key, key_path, 0, reg.KEY_WRITE)

    if run_on_startup:
        reg.SetValueEx(reg_key, app_name, 0, reg.REG_SZ, app_path)
    else:
        try:
            reg.DeleteValue(reg_key, app_name)
        except FileNotFoundError:
            pass  # Value doesn't exist, no need to remove

    # Save the setting to the config file
    settings = load_settings()
    settings["run_on_startup"] = run_on_startup
    save_settings(settings)

# Function to set the accent color on the window title bar (Windows 10+)
def set_window_accent_color(window, accent_color):
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())  # Get the window handle
    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(accent_color)), ctypes.sizeof(ctypes.c_int(accent_color)))

# GUI Setup with Loading Screen
def loading_screen():
    # Create the loading screen window
    loading_win = tk.Tk()
    loading_win.title("TempFlick - Loading...")
    loading_win.geometry("400x300")
    loading_win.resizable(False, False)  # Set window to not be resizeable

    # Set background color to dark mode
    loading_win.configure(bg="#1E1E1E")  

    # Add a loading label
    loading_label = tk.Label(
        loading_win, text="Loading TempFlick...", font=("Segoe UI", 16, "bold"),
        fg="white", bg="#1E1E1E"
    )
    loading_label.pack(expand=True)

    loading_win.update_idletasks()  # Update the UI
    loading_win.update()  # Ensure everything is displayed

    return loading_win

# GUI Setup with Dark Mode
def main():
    # Load settings (whether the app should run on startup)
    settings = load_settings()

    # Create the main window
    root = tk.Tk()
    root.title("TempFlick - Temp File Cleaner")
    
    # Set the window size to make it larger (800x500 pixels)
    root.geometry("800x500")  # Larger window size for more space
    
    # Set the window icon
    root.iconbitmap(r'B:\TempFlick\dist\tempflickicon.ico')  # Update the path as needed
    
    # Set background color to dark mode
    root.configure(bg="#1E1E1E")  

    # Set font style
    modern_font = ("Segoe UI", 12)

    # Add a title label
    label = tk.Label(
        root, text="Welcome to TempFlick!", font=("Segoe UI", 16, "bold"),
        fg="white", bg="#1E1E1E"
    )
    label.pack(pady=20)

    # Add a clean button
    clean_button = tk.Button(
        root, text="Clean Temp Files", font=modern_font, bg="#3A3A3A", fg="white",
        activebackground="#5A5A5A", activeforeground="white", relief="flat",
        command=clean_temp_dirs, width=20, height=2
    )
    clean_button.pack(pady=10)

    # Add the toggle for startup
    def toggle_callback():
        new_state = not settings["run_on_startup"]
        toggle_startup(new_state)  # Toggle the startup setting
        settings["run_on_startup"] = new_state
        save_settings(settings)
        if new_state:
            messagebox.showinfo("Startup", "TempFlick will now run on startup.")
        else:
            messagebox.showinfo("Startup", "TempFlick will no longer run on startup.")
    
    toggle_button = tk.Checkbutton(
        root, text="Run on Startup", font=modern_font, bg="#1E1E1E", fg="white", 
        activebackground="#5A5A5A", activeforeground="white", relief="flat",
        command=toggle_callback, variable=tk.BooleanVar(value=settings["run_on_startup"]),
        onvalue=True, offvalue=False
    )
    toggle_button.pack(pady=10)

    # Set the accent color for the window's title bar
    set_window_accent_color(root, 0x1E1E1E)  # Accent color set to match the background color

    # Add an exit button
    exit_button = tk.Button(
        root, text="Exit", font=modern_font, bg="#3A3A3A", fg="white",
        activebackground="#5A5A5A", activeforeground="white", relief="flat",
        command=root.quit, width=20, height=2
    )
    exit_button.pack(pady=10)

    # Run the main event loop
    root.mainloop()

if __name__ == "__main__":
    loading_win = loading_screen()  # Display the loading screen
    threading.Thread(target=main).start()  # Start the main application in a separate thread
    loading_win.destroy()  # Close the loading screen when done
