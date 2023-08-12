import re
import pandas as pd
import xlsxwriter
from tqdm import tqdm
import paramiko

# Function to get IP route data from a device using SSH
def get_ip_route_with_ssh(ip, username, password):
    try:
        # Connect to the device using SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip, username=username, password=password, timeout=10)

        # Execute the "show ip route" command
        stdin, stdout, stderr = ssh_client.exec_command("show ip route")

        # Read the output
        ip_route_data = stdout.read().decode()

        # Close the SSH connection
        ssh_client.close()

        return ip_route_data
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {ip}. {str(e)}")
        return None

# Load the Excel file with the saved IP route data
input_file = "EquinixRoutesBeforeChange.xlsx"

# Define device information
device_info = [
    {"ip": "10.111.237.200", "username": "device1_username", "password": "device1_password"},
    {"ip": "10.111.237.201", "username": "device2_username", "password": "device2_password"},
]

# Create a Pandas DataFrame for each worksheet in the Excel file
dfs = []
for sheet_name in tqdm(pd.ExcelFile(input_file).sheet_names, desc="Loading Excel data"):
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    dfs.append(df)

# Create a dictionary to store the differences between the two sets of IP route data
differences = {}

# Retrieve the "show ip route" output for the devices and compare the data
for device in tqdm(device_info, desc="Retrieving and comparing IP routes"):
    ip = device["ip"]
    username = device["username"]
    password = device["password"]
    ip_route_data[ip] = get_ip_route_with_ssh(ip, username, password)

    # Compare the IP route data for this device
    df = dfs[device_info.index(device)]  # Get the corresponding DataFrame
    route_entries = df["Route Data"].tolist()
    route_output = ip_route_data[ip]
    route_entries_new = route_output.split("\n")

    for index, route_entry in enumerate(route_entries):
        if route_entry not in route_entries_new:
            if ip not in differences:
                differences[ip] = []
            differences[ip].append({
                "index": index,
                "old_route": route_entry,
            })

# Save the differences to an Excel file with separate sheets for original data and comparison results
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the original IP route data to separate sheets
    for device, df in zip(device_info, dfs):
        df.to_excel(writer, sheet_name=f"Device_{device['ip']}", index=False)

    # Write the comparison results to a separate sheet
    for ip, diff_list in tqdm(differences.items(), desc="Writing comparison to Excel"):
        diff_df = pd.DataFrame(diff_list, columns=["Index", "Old Route"])
        diff_df.to_excel(writer, sheet_name=f"Comparison_{ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
