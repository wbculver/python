import re
import pandas as pd
import xlsxwriter
import paramiko
from tqdm import tqdm

# Variables
username = "xx"
password = "xx"

# List of device IP addresses to download "show ip route" from
device_ips = [
    "10.145.64.21",
]

# Function to retrieve "show ip route" for a device and remove timestamps
def get_ip_route_without_timestamps(device_ip):
    # SSH connection parameters
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the device
        ssh_client.connect(device_ip, username=username, password=password)

        # Create an SSH shell channel
        channel = ssh_client.invoke_shell()

        # Send the "show ip route" command
        channel.send("show ip route\n")

        # Wait for the command to complete and receive the output
        output = ""
        while not channel.recv_ready():
            pass
        while channel.recv_ready():
            output += channel.recv(1024).decode()

        # Disconnect from the device
        channel.close()
        ssh_client.close()

        # Define a regex pattern to match the timestamp format (e.g., 00:00:00 or 12:34:56)
        pattern = re.compile(r'\d{2}:\d{2}:\d{2}')

        # Remove timestamps from each line
        ip_route_output = "\n".join([pattern.sub('', line) for line in output.split("\n")])

        return ip_route_output
    except Exception as e:
        print(f"Error connecting to {device_ip}: {str(e)}")
        return ""

# Function to save IP route data to an Excel file
def save_ip_route_to_excel(data, output_file):
    # Create a Pandas DataFrame
    df = pd.DataFrame({"Route Data": data})
    # Create a Pandas Excel writer using XlsxWriter as the engine
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Write the DataFrame to a worksheet
        df.to_excel(writer, sheet_name="All Routes", index=False)

# Retrieve "show ip route" without timestamps for each device (AFTER) with tqdm
ip_route_data_after = {}
for ip in tqdm(device_ips, desc="Retrieving routes"):
    route_output_after = get_ip_route_without_timestamps(ip)
    ip_route_data_after[ip] = route_output_after

# Save all routes in separate sheets within the same Excel file
output_file = "EquinixRoutesComparison.xlsx"
with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    for ip in device_ips:
        # Save the initial routes in the first sheet
        df_initial = pd.DataFrame({"Route Data": ip_route_data_after[ip].split("\n")})
        df_initial.to_excel(writer, sheet_name=f"Initial - {ip}", index=False)

        # Compare the routes before and after
        df_changes = pd.DataFrame(columns=["Change Type", "Before", "After"])

        # Filter the initial data for the current device IP
        initial_routes = df_initial["Route Data"].astype(str).tolist()

        # Retrieve the route data after the change
        route_after = ip_route_data_after.get(ip, "").split("\n")

        # Find changes
        for route_before, route_after in zip(initial_routes, route_after):
            if route_before.strip() != route_after.strip():
                df_changes = df_changes.append({"Change Type": "Route Data", "Before": route_before.strip(), "After": route_after.strip()}, ignore_index=True)

        # Save changes to a separate sheet
        df_changes.to_excel(writer, sheet_name=f"Changes - {ip}", index=False)

print(f"Show IP Route data comparison saved to {output_file}")
