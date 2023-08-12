from netmiko import ConnectHandler
import re
import pandas as pd
import xlsxwriter
from tqdm import tqdm

# Variables
username = input("Enter your username: ")
password = input("Enter your password: ")

# List of device IP addresses to compare "show ip route" with the previous script output
device_ips = [
    "10.111.237.200",
    "10.111.237.201",
]

# Load the previous script output
previous_output_file = "EquinixRoutesAfterChange.xlsx"
previous_ip_route_data = {}

xls = pd.ExcelFile(previous_output_file)
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    previous_ip_route_data[sheet_name] = df["Route Data"].tolist()

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

# Create a dictionary to store the current "show ip route" output for each device
current_ip_route_data = {}

# Retrieve current "show ip route" without timestamps for each device
for ip in tqdm(device_ips, desc="Retrieving current IP routes"):
    current_ip_route_data[ip] = get_ip_route_without_timestamps(ip)

# Create a new Excel file to store the original, new, and comparison data
output_file = "EquinixRoutesComparison.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    for ip, current_route_output in current_ip_route_data.items():
        sheet_name = re.sub(r'[\/:*?"<>|]', '_', ip)

        # Original routes from the previous script output
        original_routes = previous_ip_route_data.get(sheet_name, [])
        
        # Ensure both lists have the same length
        max_len = max(len(original_routes), len(current_route_output.split("\n")))
        original_routes = original_routes + [''] * (max_len - len(original_routes))
        new_routes = current_route_output.split("\n") + [''] * (max_len - len(current_route_output.split("\n")))
        
        df_original = pd.DataFrame({"Original Routes": original_routes, "New Routes": new_routes})
        df_original.to_excel(writer, sheet_name=f"{sheet_name}_Comparison", index=False)

# Print the path to the output file
print(f"Route comparison data saved to {output_file}")
