from netmiko import ConnectHandler
import re
import pandas as pd

# Function to retrieve "show ip route" for a device
def get_ip_route(device_ip, username, password, enable_password):
    # Cisco device information
    device = {
        "device_type": "cisco_ios",  # Use the appropriate device type for your ASR
        "ip": device_ip,
        "username": username,
        "password": password,
        "secret": enable_password,  # If you need to enter enable mode
    }

    # Connect to the device
    net_connect = ConnectHandler(**device)

    # Enter enable mode if needed
    net_connect.enable()

    # Send the "show ip route" command and retrieve the output
    output = net_connect.send_command("show ip route")

    # Disconnect from the device
    net_connect.disconnect()

    # Define a regex pattern to match the timestamp format (e.g., 00:00:00 or 12:34:56)
    pattern = re.compile(r'\d{2}:\d{2}:\d{2}')

    # Remove timestamps from each line
    ip_route_output = "\n".join([pattern.sub('', line) for line in output.split("\n")])

    return ip_route_output

# List of device IP addresses to download "show ip route" from
device_ips = ["192.168.1.1", "192.168.1.2"]  # Add more IP addresses as needed

# Create a dictionary to store the "show ip route" output for each device
ip_route_data = {}

# Retrieve "show ip route" for each device
for ip in device_ips:
    ip_route_output = get_ip_route(ip, "YOUR_USERNAME", "YOUR_PASSWORD", "YOUR_ENABLE_PASSWORD")
    ip_route_data[ip] = ip_route_output

# Create a Pandas DataFrame from the dictionary
df = pd.DataFrame(ip_route_data.items(), columns=["Device IP", "Show IP Route"])

# Save the DataFrame to an Excel file
output_file = "show_ip_route_output.xlsx"
df.to_excel(output_file, index=False)

print(f"Show IP Route data saved to {output_file}")
