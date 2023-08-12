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
    # Exclude 10.111.237.201
]

# Load the previous script output (before change)
before_output_file = "EquinixRoutesBeforeChange.xlsx"
before_ip_route_data = {}

xls_before = pd.ExcelFile(before_output_file)
for sheet_name in xls_before.sheet_names:
    df = pd.read_excel(xls_before, sheet_name=sheet_name)
    before_ip_route_data[sheet_name] = df["Route Data"].dropna().tolist()

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

# Create a new Excel file to store the comparison data
output_file = "EquinixRoutesComparison.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    for ip in tqdm(device_ips, desc="Retrieving and comparing IP routes"):
        sheet_name = re.sub(r'[\/:*?"<>|]', '_', ip)

        # Retrieve the current "show ip route" output for the device
        current_route_output = get_ip_route_without_timestamps(ip)

        # Original routes from the before script output
        original_routes = before_ip_route_data.get(sheet_name, [])
        new_routes = current_route_output.split("\n")

        # Filter out blank lines and routes enclosed in square brackets []
        original_routes = [route.strip() for route in original_routes if route.strip() and not re.match(r'^\[.*\]$', route.strip())]
        new_routes = [route.strip() for route in new_routes if route.strip() and not re.match(r'^\[.*\]$', route.strip())]

        # Identify changed routes
        changed_routes = [route for route in new_routes if route not in original_routes]

        # Create a DataFrame for the changed routes with previous route
        df_changed_routes = pd.DataFrame({
            "Changed Routes": changed_routes,
        })

        # Add a column for the previous route
        df_changed_routes["Previous Routes"] = df_changed_routes["Changed Routes"].apply(
            lambda route: [original for original in original_routes if original.startswith(route.split()[0])]
        )

        # Write the changed routes with previous route to the Excel sheet
        df_changed_routes.to_excel(writer, sheet_name=sheet_name, index=False)

# Print the path to the output file
print(f"Route comparison data (changed routes with previous routes) saved to {output_file}")
