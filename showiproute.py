from netmiko import ConnectHandler
import re
import csv

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
    # Add the device IP address as a header
    ip_route_data.append(f"Routes for Device IP: {ip}\n")
    ip_route_output = get_ip_route_without_timestamps(ip)
    ip_route_data.append(ip_route_output)

# Save the IP route data to a CSV file
output_file = "EquinixRoutesBeforeChange.csv"
with open(output_file, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    for route_output in ip_route_data:
        # Split the route output into lines and write each line as a separate row
        for line in route_output.split('\n'):
            csv_writer.writerow([line])

print(f"Show IP Route data (without timestamps) saved to {output_file}")
