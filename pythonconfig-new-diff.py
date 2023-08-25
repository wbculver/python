from netmiko import ConnectHandler

# Device information
device_ip = "10.111.237.162"
device_username = "admin"
device_password = "admin"
device_type = "cisco_ios"

# Read the new changes from the text file
new_changes_file_path = "new_changes.txt"
with open(new_changes_file_path, "r") as f:
    new_changes_to_apply = f.read()

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
    print("Applying configuration changes...")

    # Apply the changes from the new_changes.txt file
    config_commands = [
        "configure terminal",
        new_changes_to_apply,
        "end"
    ]

    output = ""
    for cmd in config_commands:
        output += net_connect.send_command_timing(cmd + "\n")
        print(output)

print("Configuration update completed.")
