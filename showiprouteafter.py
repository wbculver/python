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
            "timeout": 120,
            "global_delay_factor": 2,
            "use_keys": False,
        }

        # Establish SSH connection to the device
        net_connect = ConnectHandler(**device)

        # Send the "show ip route" command and wait for a blank line (console clear)
        output = net_connect.send_command("show ip route", expect_string="\n")

        # Close the SSH connection
        net_connect.disconnect()

        # Remove timestamps from the output
        output_without_timestamps = re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        traceback.print_exc()
        return None

# Load the Excel file with the saved IP route data (before changes)
input_file_before = "EquinixRoutesBeforeChange.xlsx"

# Load the Excel file with the saved IP route data (after changes)
input_file_after = "EquinixRoutesAfterChange.xlsx"

# Prompt for the username and password
username = input("Enter your username: ")
password = input("Enter your password: ")

# Define device IP addresses to retrieve "show ip route" from
device_ips = [
    "10.145.32.20",
    "10.145.32.21",
    # ... add more device IPs as needed
]

# Create a Pandas DataFrame for each worksheet in the Excel file (before changes)
dfs_before = []
for sheet_name in tqdm(pd.ExcelFile(input_file_before).sheet_names, desc="Loading Excel data (before)"):
    df = pd.read_excel(input_file_before, sheet_name=sheet_name)
    dfs_before.append(df)

# Create a dictionary to store the "after" IP route data
ip_route_data_after = {}

# Retrieve the "show ip route" output for the devices (after changes)
for device_ip in tqdm(device_ips, desc="Retrieving IP routes (after)"):
    ip_route_data_after[device_ip] = get_ip_route_without_timestamps(device_ip, username, password)

# Create a Pandas DataFrame for each "after" IP route data
dfs_after = []
for device_ip in device_ips:
    data = ip_route_data_after.get(device_ip, None)
    if data:
        df = pd.DataFrame(data.split("\n"), columns=["Route Data"])
        dfs_after.append(df)
    else:
        print(f"No data for {device_ip} (after changes)")

# Create a dictionary to store the differences between the "before" and "after" IP route data
differences = {}

# Compare the IP route data for each device
for device_ip, df_before, df_after in tqdm(zip(device_ips, dfs_before, dfs_after), desc="Comparing IP routes"):
    route_entries_before = df_before["Route Data"].tolist()
    route_entries_after = df_after["Route Data"].tolist()

    diff_list = []
    for index, route_entry_before in enumerate(route_entries_before):
        if route_entry_before not in route_entries_after:
            diff_list.append({
                "index": index,
                "old_route": route_entry_before,
            })
    
    differences[device_ip] = diff_list

# Save the differences to an Excel file with separate sheets for "before", "after", and comparison results
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the original IP route data (before changes) to separate sheets
    for device_ip, df in zip(device_ips, dfs_before):
        df.to_excel(writer, sheet_name=f"Device_{device_ip}_Before", index=False)

    # Write the "after" IP route data to separate sheets
    for device_ip, df in zip(device_ips, dfs_after):
        df.to_excel(writer, sheet_name=f"Device_{device_ip}_After", index=False)

    # Write the comparison results to separate sheets
    for device_ip, diff_list in tqdm(differences.items(), desc="Writing comparison to Excel"):
        diff_df = pd.DataFrame(diff_list, columns=["Index", "Old Route"])
        diff_df.to_excel(writer, sheet_name=f"Comparison_{device_ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
