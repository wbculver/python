import re
import pandas as pd
from tqdm import tqdm
from paramiko import SSHClient, AutoAddPolicy
import traceback

# Function to retrieve "show ip route" for a device and remove timestamps
def get_ip_route_without_timestamps(device_ip, username, password):
    try:
        # Establish SSH connection to the device
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(device_ip, username=username, password=password, timeout=120)

        # Execute the "show ip route" command
        command = "show ip route"
        stdin, stdout, stderr = ssh_client.exec_command(command)

        # Read the command output
        output = stdout.read().decode("utf-8")

        # Close the SSH connection
        ssh_client.close()

        # Remove timestamps from the output
        output_without_timestamps = re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis
        return None

# Load the Excel file with the saved IP route data
input_file = "EquinixRoutesBeforeChange.xlsx"

# Prompt for the username and password
username = input("Enter your username: ")
password = input("Enter your password: ")

# Define device IP addresses to download "show ip route" from
device_ips = [
    "10.145.32.20",
    "10.145.32.21",
    "10.128.1.4",
    "10.128.1.5",
    "10.145.64.20",
    "10.145.64.21",
    "10.128.2.153",
    "10.128.2.154",
]

# Create a Pandas DataFrame for each worksheet in the Excel file (before change)
dfs_before = []
for sheet_name in tqdm(pd.ExcelFile(input_file).sheet_names, desc="Loading Excel data (before)"):
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    dfs_before.append(df)
