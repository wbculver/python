import re
import pandas as pd
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
        }

        # Establish SSH connection to the device
        net_connect = ConnectHandler(**device)

        # Send the "show ip route" command
        output = net_connect.send_command("show ip route")

        # Close the SSH connection
        net_connect.disconnect()

        # Remove timestamps from the output
        output_without_timestamps = re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis
        return None

# Load the Excel file with the saved IP route data (before change)
input_file = "EquinixRoutesBeforeChange.xlsx"

# Prompt for the username and password
username = input("Enter your username: ")
password = input("Enter your password: ")

# Define device IP addresses to download "show ip route" from
device_ips = [
    "10.111.237.200",
    "10.111.237.201",
    # Add more devices as needed
]

# Create a Pandas DataFrame for the "before" route data
dfs_before = pd.read_excel(input_file, sheet_name=None)

# Create a dictionary to store the differences between the "before" and current IP route data
differences = {}

# Retrieve the current "show ip route" output for the devices and compare the data
ip_route_data = {}  # Initialize the ip_route_data dictionary
for device_ip in device_ips:
    try:
        ip_route_data[device_ip] = get_ip_route_without_timestamps(device_ip, username, password)

        # Compare the IP route data for this device
        df_before = dfs_before[device_ip]  # Get the corresponding DataFrame (before change)
        route_entries_before = set(df_before["Route Data"].tolist())
        route_output = ip_route_data[device_ip]
        route_entries_after = set(route_output.split("\n"))

        # Find the differences between the two sets of route entries
        diff_entries = route_entries_before.symmetric_difference(route_entries_after)

        # Store the differences
        if diff_entries:
            differences[device_ip] = diff_entries
    except Exception as e:
        print(f"An error occurred while processing {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis

# Save the "before" and "after" route data, and differences to an Excel file
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the original IP route data (before change) to separate sheets
    for device_ip, df in dfs_before.items():
        df.to_excel(writer, sheet_name=f"Before_Device_{device_ip}", index=False)

    # Write the current IP route data (after change) to separate sheets
    for device_ip, route_output in ip_route_data.items():
        # Create a DataFrame without timestamps
        df_after = pd.DataFrame({"Route Data": [re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", route_output)]})
        df_after.to_excel(writer, sheet_name=f"After_Device_{device_ip}", index=False)

    # Write the differences to a separate sheet for each device
    for device_ip, diff_entries in differences.items():
        df_diff = pd.DataFrame({"Different Route Data": list(diff_entries)})
        df_diff.to_excel(writer, sheet_name=f"Differences_Device_{device_ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
