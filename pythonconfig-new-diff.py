from netmiko import ConnectHandler
from tqdm import tqdm
import difflib

# Device information
device_ip = "10.111.237.162"
device_username = "admin"
device_password = "admin"
device_type = "cisco_ios"

# Read the last applied change from the text file
last_change_file = "last_change.txt"
with open(last_change_file, "r") as f:
    last_applied_change = f.read()

# Find the position of the last applied change in the full running configuration
with open("full_running_config.txt", "r") as f:
    full_running_config = f.read()

last_change_position = full_running_config.find(last_applied_change)

# Extract the portion of the full running config after the last applied change
running_config_after_last_change = full_running_config[last_change_position + len(last_applied_change):]

# Read the new changes to apply from a separate text file
with open("new_changes.txt", "r") as f:
    new_changes_to_apply = f.read()

# Normalize the content for comparison
new_changes_normalized = new_changes_to_apply.strip()
running_config_normalized = running_config_after_last_change.strip()

# Use difflib to compare and highlight differences
diff = difflib.unified_diff(running_config_normalized.splitlines(), new_changes_normalized.splitlines(), lineterm='')

# Check if there are any differences
differences_exist = any(line.startswith('+ ') for line in diff)

# Connect to the device
with ConnectHandler(**{
    "ip": device_ip,
    "username": device_username,
    "password": device_password,
    "device_type": device_type,
    "global_delay_factor": 3,
    "timeout": 300,
    "global_cmd_verify": False,
}) as net_connect:
    # If there are differences, apply the changes
    if differences_exist:
        print("New configuration changes found, applying changes...")

        # Mark differences with "x" and create a list of marked lines
        marked_changes = []
        for line in diff:
            if line.startswith('+ '):
                marked_changes.append(f"x {line[2:]}")
            else:
                marked_changes.append(line)

        # Write marked changes to an output file
        with open("output_changes.txt", "w") as output_file:
            output_file.write("\n".join(marked_changes))

        # Apply the changes
        config_commands = [
            "configure terminal",
            "\n".join(new_changes_normalized.splitlines()),
            "end"
        ]

        output = ""
        for cmd in config_commands:
            output += net_connect.send_command_timing(cmd + "\n")
            print(output)

        # Update the last applied change in the text file
        with open(last_change_file, "w") as f:
            f.write(new_changes_normalized)
    else:
        print("No new configuration changes needed.")

print("Configuration update completed.")
