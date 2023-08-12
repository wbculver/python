import re
import pandas as pd
import xlsxwriter
from tqdm import tqdm
from netmiko import ConnectHandler

# Function to retrieve "show ip route" for a device and remove timestamps
def get_ip_route_without_timestamps(device_ip, username, password):
    try:
        # Cisco device information
        device = {
            "device_type": "cisco_ios",
            "ip": device_ip,
            "username": username,
            "password": password,
            "timeout": 120,  # Increase the timeout to 120 seconds (or more) if needed
            "global_delay_factor": 2,  # Add a delay factor to allow more time for the command output
        }

        # Establish SSH connection to the device
        net_connect = ConnectHandler(**device)

        # Send the "show ip route" command
        # Explicitly set the expected pattern to wait for
        output = net_connect.send_command("show ip route", expect_string=r"VA-EQX-HUM-A1-1-R1#")

        # Close the SSH connection
        net_connect.disconnect()

        # Remove timestamps from the output
        output_without_timestamps = re.sub(r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2}\s", "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        return None

# Load the Excel file with the saved IP route data
input_file = "EquinixRoutesBeforeChange.xlsx"

# Prompt for the username and password
username = input("Enter your username: ")
password = input("Enter your password: ")

# Define device IP addresses to download "show ip route" from
device_ips = [
    "10.111.237.200",
    "10.111.237.201",
    # Add more device IPs as needed
]

# Create a Pandas DataFrame for each worksheet in the Excel file
dfs = []
for sheet_name in tqdm(pd.ExcelFile(input_file).sheet_names, desc="Loading Excel data"):
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    dfs.append(df)

# Create a dictionary to store the differences between the two sets of IP route data
differences = {}

# Retrieve the "show ip route" output for the devices and compare the data
ip_route_data = {}  # Initialize the ip_route_data dictionary
for device_ip in tqdm(device_ips, desc="Retrieving and comparing IP routes"):
    ip_route_data[device_ip] = get_ip_route_without_timestamps(device_ip, username, password)

    # Compare the IP route data for this device
    df = dfs[device_ips.index(device_ip)]  # Get the corresponding DataFrame
    route_entries = df["Route Data"].tolist()
    route_output = ip_route_data[device_ip]
    route_entries_new = route_output.split("\n")

    for index, route_entry in enumerate(route_entries):
        if route_entry not in route_entries_new:
            if device_ip not in differences:
                differences[device_ip] = []
            differences[device_ip].append({
                "index": index,
                "old_route": route_entry,
            })

# Save the differences to an Excel file with separate sheets for original data and comparison results
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the original IP route data to separate sheets
    for device_ip, df in zip(device_ips, dfs):
        df.to_excel(writer, sheet_name=f"Device_{device_ip}", index=False)

    # Write the comparison results to a separate sheet
    for device_ip, diff_list in tqdm(differences.items(), desc="Writing comparison to Excel"):
        diff_df = pd.DataFrame(diff_list, columns=["Index", "Old Route"])
        diff_df.to_excel(writer, sheet_name=f"Comparison_{device_ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
