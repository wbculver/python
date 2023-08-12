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

        # Send the "show ip route" command and wait for a prompt
        output = net_connect.send_command("show ip route", expect_string=r"#")

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

# Create a list to store the "after" IP route data (to be filled later)
dfs_after = []

# Create a dictionary to store the differences between the "before" and "after" IP route data
differences = {}

# Retrieve the "show ip route" output for the devices (after changes) and compare the data
for device_ip in tqdm(device_ips, desc="Retrieving and comparing IP routes"):
    try:
        # Retrieve "show ip route" output after changes
        data_after = get_ip_route_without_timestamps(device_ip, username, password)
        if data_after is None:
            continue  # Skip this device if no data is retrieved

        # Convert "after" data to a list of route entries
        route_entries_after = data_after.split("\n")

        # Get the corresponding "before" DataFrame
        df_before = dfs_before[device_ips.index(device_ip)]

        # Convert "before" DataFrame to a list of route entries
        route_entries_before = [re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", entry) for entry in df_before["Route Data"].tolist()]

        # Find the differences
        diff_indices = [i for i, (r_before, r_after) in enumerate(zip(route_entries_before, route_entries_after)) if r_before != r_after]
        if diff_indices:
            differences[device_ip] = [(i, route_entries_before[i]) for i in diff_indices]

        # Append the "after" data to the list
        dfs_after.append(data_after)

    except Exception as e:
        print(f"An error occurred while processing {device_ip}. {str(e)}")
        traceback.print_exc()

# Save the differences to an Excel file with separate sheets for "before," "after," and differences
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the "before" IP route data to separate sheets
    for device_ip, df_before in zip(device_ips, dfs_before):
        df_before.to_excel(writer, sheet_name=f"Device_{device_ip}_Before", index=False)

    # Write the "after" IP route data to separate sheets
    for device_ip, data_after in zip(device_ips, dfs_after):
        if data_after is not None:
            df_after = pd.DataFrame(data_after.split("\n"), columns=["Route Data"])
            df_after.to_excel(writer, sheet_name=f"Device_{device_ip}_After", index=False)

    # Write the differences to a separate sheet
    for device_ip, diff_list in tqdm(differences.items(), desc="Writing comparison to Excel"):
        diff_df = pd.DataFrame(diff_list, columns=["Index", "Route"])
        diff_df.to_excel(writer, sheet_name=f"Differences_{device_ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
