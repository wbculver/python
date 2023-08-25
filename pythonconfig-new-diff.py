from netmiko import ConnectHandler
import yaml
import hashlib
from tqdm import tqdm

# Device information
device_ip = "10.111.237.162"
device_username = "admin"
device_password = "admin"
device_type = "cisco_ios"

# Load configuration changes from YAML file
yaml_file = "config.yaml"
with open(yaml_file) as f:
    config_changes = yaml.safe_load(f)["config_changes"]

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
    running_config = net_connect.send_command("show running-config")

    # Calculate MD5 hash of running configuration
    running_config_hash = hashlib.md5(running_config.encode()).hexdigest()

    # Loop through each change in config_changes
    for change in tqdm(config_changes, desc="Applying Configuration Changes", unit="change"):
        # Calculate MD5 hash of proposed change
        change_hash = hashlib.md5(change.encode()).hexdigest()
        
        if change_hash == running_config_hash:
            print("No configuration changes needed.")
        else:
            print("Configuration differs, applying changes...")
            
            config_commands = [
                "configure terminal",
                change,
                "end"
            ]

            output = ""
            for cmd in config_commands:
                output += net_connect.send_command_timing(cmd + "\n")
                print(output)

print("Configuration update completed.")
