from netmiko import ConnectHandler
import re
import pandas as pd

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

# Create a list to store the "show ip route" output for each device
ip_route_data = []

# Retrieve "show ip route" without timestamps for each device
for ip in device_ips:
    # Add the device IP address as a header (styled with bold and blue)
    header = f"\033[1m\033[34mRoutes for Device IP: {ip}\033[0m\n"  # Bold and blue
    ip_route_data.append(header)
    ip_route_output = get_ip_route_without_timestamps(ip)
    ip_route_data.append(ip_route_output)

# Create a Pandas DataFrame from the list
df = pd.DataFrame(ip_route_data, columns=["Route Data"])

# Save the DataFrame to an Excel file with formatting
output_file = "EquinixRoutesBeforeChange.xlsx"
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"Show IP Route data (without timestamps) saved to {output_file}")
