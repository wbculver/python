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

# Remove lines with timestamps (format: 00:00:00)
ip_route_lines = output.split("\n")
filtered_lines = [line for line in ip_route_lines if not re.match(r'^\s*\d{2}:\d{2}:\d{2}\s*', line)]

# Join the filtered lines to form the final output
ip_route_output = "\n".join(filtered_lines)

# Print the IP route without timestamps
print(ip_route_output)

# Disconnect from the device
net_connect.disconnect()
