import pandas as pd
import xlsxwriter
from tqdm import tqdm
import traceback
import netmiko
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
    # Create a ConnectHandler object
    net_connect = netmiko.ConnectHandler(
        ip=device_ip,
        username=username,
        password=password,
        device_type="cisco_ios"
    )

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
    for sheet_name in tqdm(pd.ExcelFile(input_file_before).sheet_names, desc="Loading Excel data (before)"):
        df = pd.read_excel(input_file_before, sheet_name=sheet_name)
        dfs_before.append(df)

    # Create a dictionary to store the differences between the two sets of IP route data
    differences = {}

    # Retrieve the "show ip route" output for the devices and compare the data
    for device_ip in tqdm(device_ips, desc="Retrieving and comparing IP routes"):
        try:
            # Retrieve the IP route data for the "before" data
            ip_route_before = remove_timestamps(dfs_before[device_ips.index(device_ip)]["Route Data"].str.cat(sep="\n"))

            # Retrieve the IP route data for the "after" data
            ip_route_after = get_ip_route(device_ip, username, password)
            ip_route_after = remove_timestamps(ip_route_after)

            # Compare the IP route data
            if ip_route_before != ip_route_after:
                differences[device_ip] = {
                    "before": ip_route_before,
                    "after": ip_route_after
                }
        except Exception as e:
            print(f"An error occurred while processing {device_ip}. {str(e)}")
            traceback.print_exc()  # Print the full traceback for better error analysis

    # Save the differences to an Excel file with separate sheets for original data, after data, and comparison results
    output_file = "EquinixRoutesComparisonOutput.xlsx"
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        # Write the original "before" data to a sheet
        for device_ip, df in zip(device_ips, dfs_before):
            df.to_excel(writer, sheet_name=f"Before_{device_ip}", index=False)

        # Write the "after" data to a sheet
        for device_ip, data in tqdm(differences.items(), desc="Writing 'after' data to Excel"):
            after_df = pd.DataFrame([data["after"]], columns=["Route Data"])
            after_df.to_excel(writer, sheet_name=f"After_{device_ip}", index=False)

        # Create a third sheet to show only the routes that are different
        diff_routes_df = pd.DataFrame()
        for device_ip, data in differences.items():
            # Get the differences in route data
            diff_routes = [route for route in data["before"].split("\n") if route not in data["after"]]
            # Add the differences to the DataFrame
            diff_routes_df[device_ip] = diff_routes

        # Write the third sheet to the Excel file
        diff_routes_df.to_excel(writer, sheet_name="Different_Routes", index=False)

    print(f"Differences in IP routes comparison saved to {output_file}")
