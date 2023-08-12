from netmiko import ConnectHandler
import pandas as pd
import xlsxwriter

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
    # Cisco device information
    device = {
        "device_type": "cisco_ios",  # Use the appropriate device type for your ASR
        "ip": device_ip,
        "username": username,
        "password": password,
    }

    # Connect to the device
    net_connect = ConnectHandler(**device)

    # Send the "show ip route" command and retrieve the output
    output = net_connect.send_command("show ip route")

    # Disconnect from the device
    net_connect.disconnect()

    # Remove timestamps and unnecessary information
    route_data = []
    for line in output.split("\n"):
        if "via" in line:
            route_data.append(line.strip())

    return "\n".join(route_data)

# Function to save IP route data to an Excel file
def save_ip_route_to_excel(data, output_file):
    # Create a Pandas DataFrame
    df = pd.DataFrame({"Route Data": data})
    # Create a Pandas Excel writer using XlsxWriter as the engine
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Write the DataFrame to a worksheet
        df.to_excel(writer, index=False)

# Retrieve updated "show ip route" data for each device
ip_route_data_after = {}
for ip in device_ips:
    route_output_after = get_ip_route_without_timestamps(ip)
    ip_route_data_after[ip] = route_output_after

# Load the initial route data from the previously created "before" Excel file
initial_file = "EquinixRoutesBeforeChange.xlsx"
df_initial = pd.read_excel(initial_file)

# Compare the routes before and after
changes = {}
for ip in device_ips:
    changes[ip] = []

    # Find the corresponding route table entries in the initial data
    initial_routes = df_initial[df_initial["Device IP"] == ip]["Route Data"].tolist()

    # Compare the route data before and after
    if ip in ip_route_data_after:
        route_after = ip_route_data_after[ip].split('\n')
        # Remove empty lines and leading/trailing whitespace
        route_after = [line.strip() for line in route_after if line.strip()]
        # Find changes
        for line_num, (route_before, route_after) in enumerate(zip(initial_routes, route_after), start=1):
            if route_before.strip() != route_after.strip():
                changes[ip].append(("Route Data", route_before.strip(), route_after.strip()))

# Save the changes to "EquinixRoutesAfterChange.xlsx"
output_file_after = "EquinixRoutesAfterChange.xlsx"
with pd.ExcelWriter(output_file_after, engine='xlsxwriter') as writer:
    for ip, change_data in changes.items():
        if change_data:
            # Create a DataFrame with the change information
            df_changes = pd.DataFrame(change_data, columns=["Change Type", "Before", "After"])
            # Write the DataFrame to a worksheet named after the IP address
            df_changes.to_excel(writer, sheet_name=ip, index=False)
            worksheet = writer.sheets[ip]
            # Adjust the column widths
            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 60)
            worksheet.set_column('C:C', 60)

print(f"Show IP Route data changes saved to {output_file_after}")
