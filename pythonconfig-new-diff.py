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
    last_applied_change = f.read().strip()

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
    
    # Normalize the running configuration for comparison
    running_config_normalized = "\n".join(line.strip() for line in running_config.split("\n"))

    # Find index of last applied change in the intended changes
    last_change_index = -1
    for idx, change in enumerate(intended_changes):
        if change.strip() == last_applied_change:
            last_change_index = idx
            break

    # Apply intended changes only for changes after the last applied change
    changes_to_apply = intended_changes[last_change_index + 1:]

    # Compare the intended configuration changes with the running configuration
    if "\n".join(changes_to_apply) == running_config_normalized:
        print("No new configuration changes needed.")
    else:
        print("New configuration changes found, applying changes...")
        
        # Apply the changes
        config_commands = [
            "configure terminal",
            "\n".join(changes_to_apply),
            "end"
        ]

        output = ""
        for cmd in config_commands:
            output += net_connect.send_command_timing(cmd + "\n")
            print(output)

        # Update the last applied change in the text file
        with open(last_change_file, "w") as f:
            f.write("\n".join(changes_to_apply))

print("Configuration update completed.")
