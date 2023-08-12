import re
import pandas as pd
import xlsxwriter
from tqdm import tqdm
from netmiko import ConnectHandler
import traceback

# Function to retrieve "show ip route" for a device and remove timestamps
def get_ip_route_without_timestamps(device_ip, username, password):
    try:
        # Cisco device information
        device = {
            "device_type": "cisco_ios",
            "ip": device_ip,
            "username": username,
            "password": password,
            "timeout": 120,  # Increase the timeout to 120 seconds (or more) if needed
            "global_delay_factor": 2,  # Add a delay factor to allow more time for the command output
        }

        # Establish SSH connection to the device
        net_connect = ConnectHandler(**device)

        # Send the "show ip route" command
        output = net_connect.send_command("show ip route", expect_string="") # Expect a blank line

        # Close the SSH connection
        net_connect.disconnect()

        # Remove timestamps from the output
        output_without_timestamps = re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis
        return None

# Load the Excel file with the saved IP route data before the change
input_file_before = "EquinixRoutesBeforeChange.xlsx"

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

# Create a Pandas DataFrame for each worksheet in the Excel file
dfs_before = []
for sheet_name in tqdm(pd.ExcelFile(input_file_before).sheet_names, desc="Loading Excel data (before)"):
    df = pd.read_excel(input_file_before, sheet_name=sheet_name)
    dfs_before.append(df)

# Prompt for the username and password
username = input("Enter your username: ")
password = input("Enter your password: ")

# Retrieve the "show ip route" output for the devices and compare the data
differences = {}  # Initialize the differences dictionary
for device_ip in tqdm(device_ips, desc="Retrieving and comparing IP routes"):
    try:
        route_output = get_ip_route_without_timestamps(device_ip, username, password)
        if not route_output:
            continue  # Skip this device if data retrieval failed

        # Compare the IP route data for this device with the "before" data
        df_before = dfs_before[device_ips.index(device_ip)]  # Get the corresponding DataFrame
        route_entries_before = [re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", entry) for entry in df_before["Route Data"].tolist()]
        route_entries_after = route_output.split("\n")

        # Find differences and store them in the differences dictionary
        diff_indices = []
        for index, route_entry in enumerate(route_entries_before):
            if route_entry not in route_entries_after:
                diff_indices.append(index)
        
        if diff_indices:
            differences[device_ip] = [{"index": idx, "before": route_entries_before[idx]} for idx in diff_indices]

    except Exception as e:
        print(f"An error occurred while processing {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis

# Save the differences to an Excel file with separate sheets for "before" and "after" data and differences
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the original IP route data (before change) to separate sheets
    for device_ip, df in zip(device_ips, dfs_before):
        df.to_excel(writer, sheet_name=f"Device_{device_ip}_Before", index=False)

    # Write the differences to a separate sheet for each device
    for device_ip, diff_list in tqdm(differences.items(), desc="Writing differences to Excel"):
        if not diff_list:
            continue  # Skip devices without differences
        diff_df = pd.DataFrame(diff_list, columns=["Index", "Before"])
        df_after = pd.DataFrame(route_entries_after, columns=["After"])
        # Add the "after" data as a new sheet
        df_after.to_excel(writer, sheet_name=f"Device_{device_ip}_After", index=False)
        # Add the differences as a new sheet
        diff_df.to_excel(writer, sheet_name=f"Differences_{device_ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
