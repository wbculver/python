from netmiko import ConnectHandler
import pandas as pd
import xlsxwriter

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

    # Remove timestamps from each line
    ip_route_output = "\n".join(line.split()[1:] for line in output.split("\n") if line.strip())

    return ip_route_output

# Retrieve updated "show ip route" data for each device
ip_route_data_after = {}
for ip in device_ips:
    route_output_after = get_ip_route_without_timestamps(ip)
    ip_route_data_after[ip] = route_output_after

# Load the initial route data from the previously created "before" Excel file
initial_file = "EquinixRoutesBeforeChange.xlsx"
df_initial = pd.read_excel(initial_file, header=None)

# Function to compare two sets of route data
def compare_routes(old_routes, new_routes):
    changes = []
    for line_num, (old_line, new_line) in enumerate(zip(old_routes, new_routes), start=1):
        if old_line != new_line:
            changes.append((line_num, old_line, new_line))
    return changes

# Compare the routes before and after
changes = {}
for ip in device_ips:
    changes[ip] = []

    # Find the corresponding route table entries in the initial data
    initial_routes = df_initial[df_initial[0] == ip][1].tolist()

    # Compare the route data before and after
    if ip in ip_route_data_after:
        route_after = ip_route_data_after[ip].split('\n')
        changes[ip] = compare_routes(initial_routes, route_after)

# Save the changes to "EquinixRoutesAfterChange.xlsx"
output_file_after = "EquinixRoutesAfterChange.xlsx"
with pd.ExcelWriter(output_file_after, engine='xlsxwriter') as writer:
    for ip, change_data in changes.items():
        if change_data:
            # Create a DataFrame with the change information
            df_changes = pd.DataFrame(change_data, columns=["Line Number", "Before", "After"])
            # Write
