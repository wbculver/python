import re
import pandas as pd
import xlsxwriter
from tqdm import tqdm

# Load the Excel file with the saved IP route data
input_file = "EquinixRoutesBeforeChange.xlsx"

# Create a Pandas DataFrame for each worksheet in the Excel file
dfs = []
for sheet_name in tqdm(pd.ExcelFile(input_file).sheet_names, desc="Loading Excel data"):
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    dfs.append(df)

# Retrieve the "show ip route" output for the devices
device_ips = ["10.111.237.200", "10.111.237.201"]
ip_route_data = {}
for ip in tqdm(device_ips, desc="Retrieving IP routes"):
    ip_route_data[ip] = get_ip_route_without_timestamps(ip)

# Create a dictionary to store the differences between the two sets of IP route data
differences = {}

# Compare the IP route data for each device
for ip, df in tqdm(zip(device_ips, dfs), desc="Comparing IP routes"):
    # Create a list of the route entries in the Excel file
    route_entries = df["Route Data"].tolist()

    # Create a list of the route entries in the "show ip route" output
    route_output = ip_route_data[ip]
    route_entries_new = route_output.split("\n")

    # Compare the two lists of route entries
    for index, route_entry in enumerate(route_entries):
        if route_entry not in route_entries_new:
            differences[ip] = {
                "index": index,
                "old_route": route_entry,
            }

# Save the differences to an Excel file
output_file = "EquinixRoutesAfterChange.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    for ip, differences in tqdm(differences.items(), desc="Writing to Excel"):
        df = pd.DataFrame(differences, columns=["Index", "Old Route"])
        df.to_excel(writer, sheet_name=ip, index=False)

print(f"Differences in IP routes saved to {output_file}")
