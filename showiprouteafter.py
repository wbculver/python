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

        # Compare routes and create a summary sheet
        added_routes = [route for route in new_routes if route not in original_routes]
        removed_routes = [route for route in original_routes if route not in new_routes]

        # Create DataFrames for the comparison
        df_comparison = pd.DataFrame({
            "Added Routes": added_routes,
            "Removed Routes": removed_routes,
        })

        # Filter out blank lines in the added and removed routes
        df_comparison = df_comparison[df_comparison["Added Routes"].str.strip() != ""]
        df_comparison = df_comparison[df_comparison["Removed Routes"].str.strip() != ""]

        # Write the comparison data to the Excel sheet
        df_comparison.to_excel(writer, sheet_name=f"{sheet_name}_Added_Removed", index=False)

        # Original and new route data
        df_original = pd.DataFrame(original_routes, columns=["Original Route"])
        df_new = pd.DataFrame(new_routes, columns=["New Route"])

        # Write the original and new route data to the Excel sheet
        df_original.to_excel(writer, sheet_name=f"{sheet_name}_Original", index=False)
        df_new.to_excel(writer, sheet_name=f"{sheet_name}_New", index=False)

        # Identify the changed prefix and highlight it red in the comparison sheet
        comparison_sheet_name = f"{sheet_name}_Added_Removed"
        if comparison_sheet_name in writer.sheets:
            comparison_df = pd.read_excel(writer, sheet_name=comparison_sheet_name)
            original_df = pd.read_excel(writer, sheet_name=f"{sheet_name}_Original")
            new_df = pd.read_excel(writer, sheet_name=f"{sheet_name}_New")

            # Find the changed prefixes
            changed_prefixes = comparison_df["Added Routes"].tolist()

            # Create a format for red font color
            red_font = writer.book.add_format({'font_color': 'red'})

            # Loop through the rows and highlight the changed prefixes
            for idx, row in original_df.iterrows():
                prefix = row["Original Route"]
                if prefix in changed_prefixes:
                    # Find the corresponding row index in the comparison sheet
                    comp_idx = comparison_df[comparison_df["Added Routes"] == prefix].index
                    if not comp_idx.empty:
                        comp_idx = comp_idx[0]
                        # Get the column letter for the "Added Routes" column
                        col_letter = chr(ord('A') + comparison_df.columns.get_loc("Added Routes"))
                        # Apply red font color to the corresponding cell in the comparison sheet
                        comparison_df.at[comp_idx, "Added Routes"] = f'=IF({col_letter}{comp_idx+2}="{prefix}", "{prefix}", {col_letter}{comp_idx+2})'
                        worksheet = writer.sheets[comparison_sheet_name]
                        worksheet.write_formula(f"{col_letter}{comp_idx+2}", comparison_df.at[comp_idx, "Added Routes"], red_font)

# Print the path to the output file
print(f"Route comparison data saved to {output_file}")
