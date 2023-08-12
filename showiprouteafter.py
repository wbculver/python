import pandas as pd
import re
from netmiko import ConnectHandler
import traceback

def get_ip_route_without_timestamps(device_ip, username, password):
    try:
        # Create a ConnectHandler object
        net_connect = ConnectHandler(
            ip=device_ip,
            username=username,
            password=password,
            device_type="cisco_ios"
        )

        # Execute the "show ip route" command
        output = net_connect.send_command("show ip route")

        # Close the SSH connection
        net_connect.disconnect()

        # Remove timestamps from the output
        # Remove time in format "HH:MM:SS" and variations like "5w2d" or "3w6d"
        output_without_timestamps = re.sub(r"(\d{1,2}:\d{1,2}:\d{1,2}|\d{1,4}w\d{1,2}d)\s", "", output)

        return output_without_timestamps
    except Exception as e:
        print(f"Error: Unable to retrieve IP route data from {device_ip}. {str(e)}")
        traceback.print_exc()  # Print the full traceback for better error analysis
        return None

if __name__ == "__main__":
    # Input files
    input_file_before = "EquinixRoutesBeforeChange.xlsx"
    input_file_after = "EquinixRoutesAfterChange.xlsx"

    # Prompt for the username and password
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    # Define device IP addresses to download "show ip route" from
    device_ips = [
        "10.111.237.200",
    ]

    # Create a Pandas DataFrame for each worksheet in the Excel file (before change)
    dfs_before = []
    for sheet_name in pd.ExcelFile(input_file_before).sheet_names:
        df = pd.read_excel(input_file_before, sheet_name=sheet_name, dtype=str)
        dfs_before.append(df)

    # Create a Pandas DataFrame for the "after change" Excel file
    df_after = pd.read_excel(input_file_after, dtype=str)

    # Create a dictionary to store the differences between the two sets of IP route data
    differences = {}

    # Retrieve the "show ip route" output for the devices and compare the data
    ip_route_data = {}  # Initialize the ip_route_data dictionary
    for device_ip in device_ips:
        try:
            ip_route_data[device_ip] = get_ip_route_without_timestamps(device_ip, username, password)

            # Compare the IP route data for this device
            df_before = dfs_before[device_ips.index(device_ip)]  # Get the corresponding DataFrame (before change)
            route_entries_before = [re.sub(r"(\d{1,2}:\d{1,2}:\d{1,2}|\d{1,4}w\d{1,2}d)\s", "", entry) for entry in df_before["Route Data"].tolist()]
            route_entries_after = [re.sub(r"(\d{1,2}:\d{1,2}:\d{1,2}|\d{1,4}w\d{1,2}d)\s", "", entry) for entry in df_after["Route Data"].tolist()]

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

    # Save the differences to a separate sheet in the "after change" Excel file
    output_file = "EquinixRoutesComparisonOutput.xlsx"
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        # Write the original IP route data to a sheet
        for device_ip, df in zip(device_ips, dfs_before):
            df.to_excel(writer, sheet_name=f"Device_{device_ip}", index=False)

        # Write the "after change" IP route data to a sheet
        df_after.to_excel(writer, sheet_name="AfterChange", index=False)

        # Write the comparison results to a separate sheet
        for device_ip, diff_list in differences.items():
            diff_df = pd.DataFrame(diff_list, columns=["Index", "Old Route"])
            diff_df.to_excel(writer, sheet_name=f"Differences_{device_ip}", index=False)

    print(f"Differences in IP routes comparison saved to {output_file}")
