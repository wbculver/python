from netmiko import ConnectHandler
import re
import pandas as pd
import xlsxwriter
from tqdm import tqdm

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
    # ... (same as before)

# Function to save IP route data to an Excel file
def save_ip_route_to_excel(data, output_file):
    # ... (same as before)

# Retrieve "show ip route" without timestamps for each device (AFTER)
print("Retrieving 'show ip route' data for each device...")
ip_route_data_after = {}
for ip in tqdm(device_ips, desc="Device Progress"):
    route_output_after = get_ip_route_without_timestamps(ip)
    ip_route_data_after[ip] = route_output_after

# Load the initial route data from the "before" Excel file
initial_file = "EquinixRoutesBeforeChange.xlsx"
print("Loading initial route data from 'before' file...")
df_initial = pd.read_excel(initial_file, sheet_name=None)

# Compare the routes before and after
print("Comparing 'before' and 'after' route data...")
changes = {}
for ip in tqdm(device_ips, desc="Comparison Progress"):
    changes[ip] = []

    # Filter the initial data for the current device IP
    initial_routes = df_initial[ip]["Route Data"].astype(str).tolist()

    # Retrieve the route data after the change
    route_after = ip_route_data_after.get(ip, "").split("\n")

    # Find changes
    for line_num, (route_before, route_after) in enumerate(zip(initial_routes, route_after), start=1):
        if route_before.strip() != route_after.strip():
            changes[ip].append(("Route Data", route_before.strip(), route_after.strip()))

# Save the changes to "EquinixRoutesAfterChange.xlsx"
output_file_after = "EquinixRoutesAfterChange.xlsx"
print("Saving changes to 'after' Excel file...")
with pd.ExcelWriter(output_file_after, engine='xlsxwriter') as writer:
    for ip, change_data in changes.items():
        if change_data:
            # ... (same as before)

print(f"Show IP Route data changes saved to {output_file_after}")
