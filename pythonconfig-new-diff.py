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

# Lines of text to exclude from comparison
excluded_lines = ["no logging console", "banner motd", "ntp server"]

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

    # Normalize and calculate MD5 hash for running configuration
    running_config_lines = [line.strip() for line in running_config.split("\n") if line.strip() and not line.strip().startswith("!")]
    running_config_normalized = "\n".join(line for line in running_config_lines if line not in excluded_lines)
    running_config_hash = hashlib.md5(running_config_normalized.encode()).hexdigest()

    # Calculate MD5 hash for intended configuration changes
    intended_config = "\n".join(config_changes)
    intended_config_hash = hashlib.md5(intended_config.encode()).hexdigest()

    if intended_config_hash == running_config_hash:
        print("No configuration changes needed.")
    else:
        print("Configuration differs, applying changes...")

        config_commands = [
            "configure terminal"
        ]
        
        config_commands.extend(config_changes)
        
        config_commands.append("end")

        output = ""
        for cmd in config_commands:
            output += net_connect.send_command_timing(cmd + "\n")
            print(output)

print("Configuration update completed.")
