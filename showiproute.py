from netmiko import ConnectHandler
import re

# Cisco ASR device information
device = {
    "device_type": "cisco_ios",  # Use the appropriate device type for your ASR
    "ip": "YOUR_DEVICE_IP",
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
    "secret": "YOUR_ENABLE_PASSWORD",  # If you need to enter enable mode
}

# Connect to the device
net_connect = ConnectHandler(**device)

# Enter enable mode if needed
net_connect.enable()

# Send the "show ip route" command and retrieve the output
output = net_connect.send_command("show ip route")

# Define a regex pattern to match the timestamp format (e.g., 00:00:00 or 12:34:56)
pattern = re.compile(r'\d{2}:\d{2}:\d{2}')

# Remove lines with the timestamp pattern
ip_route_output = "\n".join([line for line in output.split("\n") if not pattern.search(line)])

# Print the IP route without lines containing timestamps
print(ip_route_output)

# Disconnect from the device
net_connect.disconnect()
