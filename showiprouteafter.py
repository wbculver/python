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

# Create a dictionary to store the current "show ip route" output for each device
current_ip_route_data = {}

# Retrieve current "show ip route" without timestamps for each device
for ip in tqdm(device_ips, desc="Retrieving current IP routes"):
    current_ip_route_data[ip] = get_ip_route_without_timestamps(ip)

# Create a new Excel file to store the comparison data
output_file = "EquinixRoutesComparison.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    for ip, current_route_output in current_ip_route_data.items():
        sheet_name = re.sub(r'[\/:*?"<>|]', '_', ip)

        # Original routes from the before script output
        original_routes = before_ip_route_data.get(sheet_name, [])
        new_routes = current_route_output.split("\n")

        # Filter out blank lines before performing the comparison
        original_routes = [route for route in original_routes if route.strip()]
        new_routes = [route for route in new_routes if route.strip()]

        # Create DataFrames for the comparison
        df_comparison = pd.DataFrame({
            "Previous Routes": new_routes,
            "Changed Routes": original_routes,
        })

        # Identify the changed prefixes
        changed_prefixes = df_comparison[df_comparison["Previous Routes"] != df_comparison["Changed Routes"]]["Previous Routes"].tolist()

        # Include the previous row above the changed route
        prev_row = None
        for idx, row in df_comparison.iterrows():
            if row["Previous Routes"] in changed_prefixes:
                if prev_row:
                    df_comparison.at[idx, "Diff Out"] = prev_row
            prev_row = row["Previous Routes"]

        # Filter out blank lines in the previous and changed routes
        df_comparison = df_comparison[df_comparison["Previous Routes"].str.strip() != ""]
        df_comparison = df_comparison[df_comparison["Changed Routes"].str.strip() != ""]

        # Move entries from column C (Changed Routes) to column D (Diff Out) at the top
        df_comparison["Diff Out"].fillna(df_comparison["Changed Routes"], inplace=True)
        df_comparison.drop(columns=["Changed Routes"], inplace=True)

        # Write the comparison data to the Excel sheet
        df_comparison.to_excel(writer, sheet_name=sheet_name, index=False)

        # Highlight rows in column C (Diff Out) in red
        worksheet = writer.sheets[sheet_name]
        red_font = writer.book.add_format({'font_color': 'red'})
        worksheet.conditional_format(1, 2, df_comparison.shape[0], 2, {'type': 'text', 'criteria': 'containing', 'value': '*', 'format': red_font})

# Print the path to the output file
print(f"Route comparison data saved to {output_file}")
