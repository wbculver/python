import re
import pandas as pd
import xlsxwriter
from tqdm import tqdm
from netmiko import SSHClient, AutoAddPolicy
import traceback

# Function to retrieve "show ip route" for a device and remove timestamps
def get_ip_route_without_timestamps(device_ip, username, password):
    try:
        # Establish SSH connection to the device
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(device_ip, username=username, password=password, timeout=120)

        # Execute the "show ip route" command
        command = "show ip route"
        stdin, stdout, stderr = ssh_client.exec_command(command)

        # Read the command output
        output = stdout.read().decode("utf-8")

        # Close the SSH connection
        ssh_client.close()

        # Remove timestamps from the output
        pattern = r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2} \w{3}:\w{3}:\w{3}:\w{3}"
        output_without_timestamps = re.sub(pattern, "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis
        return None

# Load the Excel files with the saved IP route data
input_file_before = "EquinixRoutesBeforeChange.xlsx"

# Prompt for the username and password
username = input("Enter your username: ")
password = input("Enter your password: ")

# Define device IP addresses to download "show ip route" from
device_ips = [
    "10.111.237.200",
]

# Create a Pandas DataFrame for each worksheet in the Excel file (before change)
dfs_before = []
for sheet_name in tqdm(pd.ExcelFile(input_file_before).sheet_names, desc="Loading Excel data (before)"):
    df = pd.read_excel(input_file_before, sheet_name=sheet_name)
    dfs_before.append(df)

# Create a dictionary to store the differences between the two sets of IP route data
differences = {}

# Retrieve the "show ip route" output for the devices and compare the data
ip_route_data = {}  # Initialize the ip_route_data dictionary
for device_ip in tqdm(device_ips, desc="Retrieving and comparing IP routes"):
    try:
        ip_route_data[device_ip] = get_ip_route_without_timestamps(device_ip, username, password)

        # Compare the IP route data for this device
        df_before = dfs_before[device_ips.index(device_ip)]  # Get the corresponding DataFrame (before change)
        route_entries_before = [re.sub(pattern, "", entry) for entry in df_before["Route Data"].tolist()]
        route_output = ip_route_data[device_ip]
        route_entries_after = route_output.split("\n")

        for index, route_entry in enumerate(route_entries_before):
            if route_entry not in route_entries_after:
                if device_ip not in differences:
                    differences[device_ip] = []
                differences[device_ip].append({
                    "index": index,
                    "old_route": route_entry,
                })
    except Exception as e:
        print(f"An error occurred while processing {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis

# Save the differences to an Excel file with separate sheets for original data and comparison results
output_file = "EquinixRoutesComparisonOutput.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    # Write the original IP route data from the "before" Excel file
    for df_before, sheet_name in zip(dfs_before, pd.ExcelFile(input_file_before).sheet_names):
        df_before.to_excel(writer, sheet_name=f"Before_{sheet_name}", index=False)

    # Write the comparison results to a separate sheet
    for device_ip, diff_list in tqdm(differences.items(), desc="Writing comparison to Excel"):
        diff_df = pd.DataFrame(diff_list, columns=["Index", "Old Route"])
        diff_df.to_excel(writer, sheet_name=f"Comparison_{device_ip}", index=False)

print(f"Differences in IP routes comparison saved to {output_file}")
