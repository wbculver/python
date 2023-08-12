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

        # Send the "show ip route" command and wait for output
        net_connect.send_command("show ip route", expect_string=r"\S+")
        output = net_connect.send_command("show ip route", expect_string=r"EOF_MARKER_FOR_COMMAND_EXECUTION")

        # Close the SSH connection
        net_connect.disconnect()

        # Remove timestamps from the output
        output_without_timestamps = re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis
        return None

# Load the Excel file with the saved IP route data (before)
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

# Create a list of DataFrames to store the "before" IP route data
dfs_before = []
for device_ip in tqdm(device_ips, desc="Loading Excel data (before)"):
    df = pd.read_excel(input_file, sheet_name=device_ip)
    dfs_before.append(df)

# Create a dictionary to store the differences between the "before" and "after" sets of IP route data
differences = {}

# Retrieve the "show ip route" output for the devices and compare the data
for device_ip in tqdm(device_ips, desc="Retrieving and comparing IP routes"):
    try:
        # Get the "before" DataFrame for this device
        df_before = dfs_before[device_ips.index(device_ip)]

        # Retrieve the "after" IP route data
        route_output_after = get_ip_route_without_timestamps(device_ip, username, password)

        if route_output_after:
            # Split route entries and remove timestamps
            route_entries_before = [re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", entry) for entry in df_before["Route Data"].tolist()]
            route_entries_after = route_output_after.split("\n")

            # Find differences
            for index, route_entry in enumerate(route_entries_before):
                if route_entry not in route_entries_after:
                    if device_ip not in differences:
                        differences[device_ip] = []
                    differences[device_ip].append({
                        "index": index,
                        "before_route": route_entry,
                    })

            # Store the "after" IP route data in a new sheet in the Excel file
            df_after = pd.DataFrame({"Route Data (After)": route_entries_after})
            with pd.ExcelWriter(input_file, engine="openpyxl", mode="a") as writer:
                df_after.to_excel(writer, sheet_name=f"{device_ip}_After", index=False)
    except Exception as e:
        print(f"An error occurred while processing {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis

# Save the differences to an Excel file with a separate sheet for comparison results
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the original IP route data to separate sheets
    for device_ip, df in zip(device_ips, dfs_before):
        df.to_excel(writer, sheet_name=f"Device_{device_ip}", index=False)

    # Write the comparison results to a separate sheet
    for device_ip, diff_list in tqdm(differences.items(), desc="Writing comparison to Excel"):
        diff_df = pd.DataFrame(diff_list, columns=["Index", "Before Route"])
        diff_df.to_excel(writer, sheet_name=f"Comparison_{device_ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
