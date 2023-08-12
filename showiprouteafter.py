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
def save_ip_route_to_excel(data, output_file, sheet_name="{} Route".format(device_ip)):
    # Create a Pandas DataFrame
    df = pd.DataFrame({"Route Data": data})

    # Save the DataFrame to the Excel file
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# Retrieve the output of "show ip route" for each device
for ip in device_ips:
    route_output = get_ip_route_without_timestamps(ip)

    # Compare the output to the file EquinixRoutesBeforeChange.xlsx
    with open("EquinixRoutesBeforeChange.xlsx", "r") as f:
        equinixroutesbeforechange = f.read()

    if route_output != equinixroutesbeforechange:
        print(f"There are changes to the routes on device {ip}")

    # Save the output to the Excel file
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df = pd.DataFrame({"Route Data": route_output})
        df.to_excel(writer, sheet_name="{} Route".format(ip), index=False)

print("Done!")
