from netmiko import ConnectHandler
import re
import pandas as pd
import xlsxwriter
from tqdm import tqdm

# Variables
username = input("Enter your username: ")
password = input("Enter your password: ")

# List of device IP addresses to download "show ip route" from
device_ips = [
    "10.111.237.200",
    "10.111.237.201",
]

# Function to retrieve "show ip route" for a device and remove timestamps
def get_ip_route_without_timestamps(device_ip):
    # Cisco device information
    device = {
        "device_type": "cisco_ios",
        "ip": device_ip,
        "username": username,
        "password": password,
        "timeout": 60,  # Increase the timeout if needed
        "global_delay_factor": 2,  # Add a delay factor to allow more time for the command output
    }

    # Connect to the device
    net_connect = ConnectHandler(**device)

    try:
        # Send the "terminal length 0" command
        net_connect.send_command_timing("terminal length 0")

        # Send the "show ip route" command and retrieve the output
        output = net_connect.send_command_timing("show ip route")

        # Define regex patterns to match timestamps (e.g., 00:00:00 or 12:34:56)
        # and relative time format (e.g., 5w1d, 1d5h)
        timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}')
        relative_time_pattern = re.compile(r'\d+[wdhms]')
        
        # Remove timestamps and relative time format from each line
        ip_route_output = "\n".join([
            relative_time_pattern.sub('', timestamp_pattern.sub('', line))
            for line in output.split("\n")
        ])

        return ip_route_output
    finally:
        # Disconnect from the device
        net_connect.disconnect()

# Create a dictionary to store the "show ip route" output for each device
ip_route_data = {}

# Retrieve "show ip route" without timestamps for each device
for ip in tqdm(device_ips, desc="Retrieving IP routes"):
    ip_route_data[ip] = get_ip_route_without_timestamps(ip)

# Save the IP route data to an Excel file
output_file = "EquinixRoutesAfterChange.xlsx"

# Create a Pandas DataFrame for each device
dfs = []
for ip, route_output in ip_route_data.items():
    # Create a list of route entries with a new line for each entry
    route_entries = route_output.split("\n")
    # Create a DataFrame with a single column and the "Routes for Device IP" header
    df = pd.DataFrame(route_entries, columns=["Route Data"])
    # Remove invalid characters from sheet name
    sheet_name = re.sub(r'[\/:*?"<>|]', '_', ip)
    dfs.append((df, sheet_name))

# Create a Pandas Excel writer
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    for df, sheet_name in tqdm(dfs, desc="Writing to Excel"):
        # Write each DataFrame to a separate worksheet with the modified sheet name
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        # Adjust the column width to fit the content
        worksheet.set_column('A:A', max(len(line) for line in df["Route Data"]))

print(f"Show IP Route data (without timestamps) saved to {output_file}")
