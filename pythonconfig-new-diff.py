
from netmiko import ConnectHandler
import yaml
from tqdm import tqdm
import socket

device_ip = "10.111.237.162"
device_username = "admin"
device_password = "admin"
device_type = "cisco_ios"
yaml_file = "config.yaml"
with open(yaml_file) as f: config_changes = yaml.safe_load(f)
with ConnectHandler(**{
    "ip": device_ip,
    "username": device_username,
    "password": device_password,
    "device_type": device_type,
    "global_delay_factor": 3,
    "timeout":  300,
    "global_cmd_verify": False,

}) as net_connect: running_config = net_connect.send_command("show running-config")

for change in tqdm(config_changes, desc="Applying Configuration Changes", unit="interface"): interface = change.get("interface")
descriptions = change.get("descriptions", [])

config_snippet = f"interface {interface}\n"

config_snippet += '\n'.join(f"  description {description}"
for description
in descriptions)

if config_snippet.strip() in running_config:
  print (f"No configuration changes needed for {interface}.")
else:
  print (f"Configuration differs for {interface}, applying changes...")

config_commands = [
"configure terminal",
                config_snippet,
                "end"
            ]

output = "" 
for  cmd in config_commands:
  output += net_connect.send_command_timing(cmd
+ "\n") 
  print(output)

print("Configuration update completed.")
