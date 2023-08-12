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

# Create a Pandas DataFrame for each "after" IP route data
dfs_after = []
for device_ip in device_ips:
    # Retrieve the "show ip route" output for the devices (after changes)
    data_after = get_ip_route_without_timestamps(device_ip, username, password)
    if data_after:
        df = pd.DataFrame(data_after.split("\n"), columns=["Route Data"])
        dfs_after.append(df)
    else:
        print(f"No data for {device_ip} (after changes)")

# Save the "before" and "after" IP routes to separate sheets
with pd.ExcelWriter("EquinixRoutesComparisonOutput.xlsx", engine="xlsxwriter") as writer:
    for device_ip, df_before, df_after in tqdm(zip(device_ips, dfs_before, dfs_after), desc="Saving to Excel"):
        # Write the "before" IP route data
        df_before.to_excel(writer, sheet_name=f"Device_{device_ip}_Before", index=False)

        # Write the "after" IP route data
        if df_after:
            df_after.to_excel(writer, sheet_name=f"Device_{device_ip}_After", index=False)

# Print completion message
print("Comparison completed and saved to EquinixRoutesComparisonOutput.xlsx")
