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
    for line_num, (old_line, new_line) in enumerate(zip(old_routes, new_routes)):
        if old_line != new_line:
            changes.append((line_num + 1, old_line, new_line))
    return changes

# Retrieve "show ip route" without timestamps for each device
ip_route_data_before = {}
ip_route_data_after = {}
for ip in device_ips:
    route_output_before = get_ip_route_without_timestamps(ip)
    ip_route_data_before[ip] = route_output_before

# Save the initial IP route data to "EquinixRoutesBeforeChange.xlsx"
output_file_before = "EquinixRoutesBeforeChange.xlsx"
save_ip_route_to_excel(ip_route_data_before.values(), output_file_before)
print(f"Initial Show IP Route data (without timestamps) saved to {output_file_before}")

# Retrieve updated "show ip route" data for each device
for ip in device_ips:
    route_output_after = get_ip_route_without_timestamps(ip)
    ip_route_data_after[ip] = route_output_after

# Compare the routes before and after
changes = {}
for ip, route_before in ip_route_data_before.items():
    route_after = ip_route_data_after[ip]
    changes[ip] = compare_routes(route_before.split("\n"), route_after.split("\n"))

# Save the changes to "EquinixRoutesAfterChange.xlsx"
output_file_after = "EquinixRoutesAfterChange.xlsx"
with pd.ExcelWriter(output_file_after, engine='xlsxwriter') as writer:
    for ip, change_data in changes.items():
        # Create a DataFrame with the change information
        df_changes = pd.DataFrame(change_data, columns=["Line Number", "Before", "After"])
        # Write the DataFrame to a worksheet named after the IP address
        df_changes.to_excel(writer, sheet_name=ip, index=False)
        worksheet = writer.sheets[ip]
        # Adjust the column widths
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 60)
        worksheet.set_column('C:C', 60)

print(f"Show IP Route data changes saved to {output_file_after}")
