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
    
    # Remove all whitespace characters from running configuration
    running_config = "".join(running_config.split())

    # Apply intended changes to the running config lines
    for idx, change in enumerate(intended_changes):
        intended_changes[idx] = "".join(change.split())

    # Compare the intended configuration with the running configuration
    if "".join(intended_changes) == running_config:
        print("No configuration changes needed.")
    else:
        print("Configuration differs in intended changes, applying changes...")
        
        # Apply the changes
        config_commands = [
            "configure terminal",
            "\n".join(intended_changes),
            "end"
        ]

        output = ""
        for cmd in config_commands:
            output += net_connect.send_command_timing(cmd + "\n")
            print(output)

print("Configuration update completed.")
