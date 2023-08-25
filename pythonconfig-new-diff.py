from netmiko import ConnectHandler
import yaml
from tqdm import tqdm
import difflib

# ... (rest of the code)

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
    # Download the entire running configuration
    running_config = net_connect.send_command("show running-config")
    
    # Find the position of the last applied change in the running configuration
    last_change_position = running_config.find(last_applied_change)

    # Extract the portion of the running config after the last applied change
    running_config_after_last_change = running_config[last_change_position + len(last_applied_change):]

    # Normalize the new intended changes for comparison
    new_changes_normalized = "\n".join(line.strip() for line in new_changes_to_apply)

    # Use difflib to compare and highlight differences
    diff = difflib.unified_diff(running_config_after_last_change.splitlines(), new_changes_normalized.splitlines(), lineterm='')

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
        "\n".join(new_changes_to_apply),
        "end"
    ]

    output = ""
    for cmd in config_commands:
        output += net_connect.send_command_timing(cmd + "\n")
        print(output)

    # Update the last applied change in the text file
    with open(last_change_file, "w") as f:
        f.write("\n".join(new_changes_to_apply))

print("Configuration update completed.")
