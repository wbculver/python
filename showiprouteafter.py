from netmiko import ConnectHandler
import re
import pandas as pd
import xlsxwriter
import os

# Variables
username = "admin"
password = "Eve1234!"

# List of device IP addresses to download "show ip route" from
device_ips = [
    "10.111.237.200",
    "10.111.237.201",
]

# Function to retrieve "show ip route" for a device and remove timestamps
def get_ip_route_without_timestamps(device_ip):
    # Cisco device information
    device = {
        "device_type": "cisco_ios",  # Use the appropriate device type for your ASR
        "ip": device_ip,
        "username": username,
        "password": password,
    }

    # Connect to the device
    net_connect = ConnectHandler(**device)

    # Send the "show ip route" command and retrieve the output
    output = net_connect.send_command("show ip route")

    # Disconnect from the device
    net_connect.disconnect()

    # Define a regex pattern to match the timestamp format (e.g., 00:00:00 or 12:34:56)
    pattern = re.compile(r'\d{2}:\d{2}:\d{2}')

    # Remove timestamps from each line
    ip_route_output = "\n".join([pattern.sub('', line) for line in output.split("\n")])

    return ip_route_output

# Function to save IP route data to an Excel file
def save_ip_route_to_excel(data, output_file):
    # Create a Pandas DataFrame
    df = pd.DataFrame({"Route Data": data})
    # Create a Pandas Excel writer using XlsxWriter as the engine
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Write the DataFrame to a worksheet
        df.to_excel(writer, index=False)

# Function to compare two sets of route data
def compare_routes(old_routes, new_routes):
    changes = []
    for line_num, (old_line, new_line) in enumerate(zip(old_routes, new_routes), start=1):
        if old_line != new_line:
            changes.append((line_num, old_line, new_line))
    return changes

# Retrieve updated "show ip route" data for each device
ip_route_data_after = {}
for ip in device_ips:
    route_output_after = get_ip_route_without_timestamps(ip)
    ip_route_data_after
