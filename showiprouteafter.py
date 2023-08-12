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
        }

        # Establish SSH connection to the device
        net_connect = ConnectHandler(**device)

        # Send the "show ip route" command
        output = net_connect.send_command("show ip route")

        # Close the SSH connection
        net_connect.disconnect()

        # Remove timestamps from the output
        output_without_timestamps = re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2} \w{3}:\w{3}:\w{3}:\w{3}", "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        traceback.print_exc()
        return None

# Load the Excel file with the saved IP route data (before)
input_file = "EquinixRoutesBeforeChange.xlsx"

# Load the Excel file with the IP route data after the change
input_file_after = "EquinixRoutesAfterChange.xlsx"

# Prompt for the username and password
username = input("Enter your username: ")
password = input("Enter your password: ")

# Define device IP addresses to download "show ip route" from
device_ips = [
    "10.111.237.200",
]

# Create a Pandas DataFrame for each worksheet in the "before" Excel file
dfs_before = []
for sheet_name in tqdm(pd.ExcelFile(input_file).sheet_names, desc="Loading Excel data (before)"):
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    dfs_before.append(df)

# Create a Pandas DataFrame for the "after" Excel file
df_after = pd.read_excel(input_file_after)

# Create a dictionary to store the differences between the two sets of IP route data
differences = {}

# Retrieve the "show ip route" output for the devices and compare the data
ip_route_data = {}  # Initialize the ip_route_data dictionary
for device_ip in tqdm(device_ips, desc="Retrieving and comparing IP routes"):
    try:
        ip_route_data[device_ip] = get_ip_route_without_timestamps(device_ip, username, password)

        # Compare the IP route data for this device
        df_before = dfs_before[device_ips.index(device_ip)]  # Get the corresponding DataFrame (before change)
        route_entries_before = [re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2} \w{3}:\w{3}:\w{3}:\w{3}", "", entry) for entry in df_before["Route Data"].tolist()]
        route_output = ip_route_data[device_ip]
        route_entries_after = [re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2} \w{3}:\w{3}:\w{3}:\w{3}", "", entry) for entry in route_output.split("\n")]

        # Find differences between before and after routes
        diff_indices = [index for index, (route_before, route_after) in enumerate(zip(route_entries_before, route_entries_after)) if route_before != route_after]
        if diff_indices:
            differences[device_ip] = [{"index": index, "before": route_entries_before[index], "after": route_entries_after[index]} for index in diff_indices]
    except Exception as e:
        print(f"An error occurred while processing {device_ip}. {str(e)}")
        traceback.print_exc()

# Save the differences to an Excel file with separate sheets for original data and comparison results
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the original IP route data to separate sheets
    for device_ip, df in zip(device_ips, dfs_before):
        df.to_excel(writer, sheet_name=f"Device_{device_ip}_Before", index=False)

    # Write the "after" IP route data to a separate sheet
    df_after.to_excel(writer, sheet_name="Device_After", index=False)

    # Write the comparison results to a separate sheet
    for device_ip, diff_list in differences.items():
        diff_df = pd.DataFrame(diff_list, columns=["Index", "Before", "After"])
        diff_df.to_excel(writer, sheet_name=f"Differences_{device_ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
