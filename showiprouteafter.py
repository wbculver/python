import pandas as pd
import re
from netmiko import ConnectHandler
import traceback
from tqdm import tqdm

def get_ip_route_without_timestamps(device_ip, username, password):
    # The implementation of this function remains the same as in your original script
    # ...

if __name__ == "__main__":
    # Input file for the IP route data before the change
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
    for sheet_name in pd.ExcelFile(input_file_before).sheet_names:
        df = pd.read_excel(input_file_before, sheet_name=sheet_name, dtype=str)
        dfs_before.append(df)

    # Create a dictionary to store the differences between the two sets of IP route data
    differences = {}

    # Use tqdm to visualize the progress
    for device_ip in tqdm(device_ips, desc="Processing devices"):
        try:
            ip_route_data[device_ip] = get_ip_route_without_timestamps(device_ip, username, password)

            # Compare the IP route data for this device
            df_before = dfs_before[device_ips.index(device_ip)]  # Get the corresponding DataFrame (before change)
            route_entries_before = [re.sub(r"(\d{1,2}:\d{1,2}:\d{1,2}|\d{1,4}w\d{1,2}d)\s", "", entry) for entry in df_before["Route Data"].tolist()]

            # ... rest of the comparison code ...
            
        except Exception as e:
            print(f"An error occurred while processing {device_ip}. {str(e)}")
            traceback.print_exc()  # Print the full traceback for better error analysis

    # Save the differences to a separate sheet in the "before change" Excel file
    output_file = "EquinixRoutesComparisonOutput.xlsx"
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        # Write the original IP route data to a sheet
        for device_ip, df in zip(device_ips, dfs_before):
            df.to_excel(writer, sheet_name=f"Device_{device_ip}", index=False)

        # Write the comparison results to a separate sheet
        for device_ip, diff_list in differences.items():
            diff_df = pd.DataFrame(diff_list, columns=["Index", "Old Route"])
            diff_df.to_excel(writer, sheet_name=f"Differences_{device_ip}", index=False)

    print(f"Differences in IP routes comparison saved to {output_file}")
