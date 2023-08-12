import pandas as pd
from netmiko import ConnectHandler
import re

def remove_timestamps(data_with_timestamps):
    """Removes timestamps from the input data using a regex pattern.

    Args:
        data_with_timestamps (str): Input data with timestamps.

    Returns:
        str: Data with timestamps removed.
    """
    pattern = r"\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,2} \w{3}:\w{3}:\w{3}:\w{3}"
    return re.sub(pattern, "", data_with_timestamps)

def get_ip_route(device_ip, username, password):
    """Retrieves the IP route data from a network device.

    Args:
        device_ip (str): The IP address of the network device.
        username (str): The username to use to connect to the network device.
        password (str): The password to use to connect to the network device.

    Returns:
        str: The IP route data.
    """
    device = {
        "device_type": "cisco_ios",
        "ip": device_ip,
        "username": username,
        "password": password,
    }

    # Establish SSH connection to the device
    net_connect = ConnectHandler(**device)

    # Execute the "show ip route" command
    command = "show ip route"
    output = net_connect.send_command(command)

    # Close the SSH connection
    net_connect.disconnect()

    return output

if __name__ == "__main__":
    input_file_before = "EquinixRoutesBeforeChange.xlsx"

    # Prompt for the username and password
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    # Define device IP addresses to download "show ip route" from
    device_ips = [
        "10.111.237.200",
    ]

    # Create a Pandas DataFrame for each worksheet in the "before" Excel file
    dfs_before = []
    for sheet_name in pd.ExcelFile(input_file_before).sheet_names:
        df = pd.read_excel(input_file_before, sheet_name=sheet_name)
        dfs_before.append(df)

    # Create a dictionary to store the differences between the two sets of IP route data
    differences = {}

    # Retrieve the "show ip route" output for the devices and compare the data
    for device_ip in device_ips:
        try:
            # Retrieve the IP route data for the "before" data
            ip_route_before = dfs_before[device_ips.index(device_ip)]["Route Data"].str.cat(sep="\n")

            # Retrieve the IP route data for the "after" data
            ip_route_after = get_ip_route(device_ip, username, password)

            # Compare the IP route data
            if ip_route_before != ip_route_after:
                differences[device_ip] = {
                    "before": ip_route_before,
                    "after": ip_route_after
                }
        except Exception as e:
            print(f"An error occurred while processing {device_ip}. {str(e)}")

    # Save the differences to an Excel file with separate sheets
    output_file = "EquinixRoutesComparisonOutput.xlsx"
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        for device_ip, data in differences.items():
            # Write the "before" data to a sheet
            dfs_before[device_ips.index(device_ip)].to_excel(writer, sheet_name=f"Before_{device_ip}", index=False)
            
            # Write the "after" data to a sheet
            df_after = pd.DataFrame({"Route Data": data["after"].split("\n")})
            df_after.to_excel(writer, sheet_name=f"After_{device_ip}", index=False)
            
            # Write the differences to a sheet
            diff_routes = [route for route in data["before"].split("\n") if route not in data["after"]]
            df_diff = pd.DataFrame({"Different Routes": diff_routes})
            df_diff.to_excel(writer, sheet_name=f"Difference_{device_ip}", index=False)

    print(f"Differences in IP routes comparison saved to {output_file}")
