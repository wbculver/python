from netmiko import ConnectHandler
import yaml
from tqdm import tqdm

# Device information
device_ip = "10.111.237.162"
device_username = "admin"
device_password = "admin"
device_type = "cisco_ios"

# Load intended configuration changes from YAML file
yaml_file = "config.yaml"
with open(yaml_file) as f:
    config_data = yaml.safe_load(f)

# Extract intended changes from the YAML file
intended_changes = config_data.get("config_changes", [])

# Read the last applied change from the text file
last_change_file = "last_change.txt"
with open(last_change_file, "r") as f:
    last_applied_change = f.read()

# Find the index of the last applied change in intended_changes
last_change_index = -1
for idx, change in enumerate(intended_changes):
    if change.strip() == last_applied_change.strip():
        last_change_index = idx
        break

# Extract new intended changes to compare
new_changes_to_apply = intended_changes[last_change_index + 1:]

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

    # Compare new intended changes with the running configuration portion
    if new_changes_normalized in running_config_after_last_change:
        print("No new configuration changes needed.")
    else:
        print("New configuration changes found, applying changes...")
        
        # Mark differences with "x"
        marked_changes = []
        for line in running_config_after_last_change.splitlines():
            if line.strip() == new_changes_normalized:
                marked_changes.append(line)
            else:
                marked_changes.append(f"x {line}")

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
