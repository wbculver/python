from netmiko import ConnectHandler
from tqdm import tqdm  # Import tqdm for the progress bar

# Prompt user for device credentials
device_ip = input("Enter the device IP: ")
device_username = input("Enter the device username: ")
device_password = input("Enter the device password: ")
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
    print("Downloading the latest running configuration...")

    # Download the running configuration
    running_config = net_connect.send_command("show running-config")

    # Save the running configuration to a file
    running_config_file_path = "running_config.txt"
    with open(running_config_file_path, "w") as f:
        f.write(running_config)

    print("Running configuration saved to:", running_config_file_path)

    print("Applying configuration changes...")

    # Apply the changes from the new_changes.txt file
    config_commands = [
        "configure terminal",
        new_changes_to_apply,
        "end"
    ]

    output = ""
    with tqdm(total=len(config_commands), desc="Progress", unit="step") as pbar:
        for cmd in config_commands:
            output += net_connect.send_command_timing(cmd + "\n")
            pbar.update(1)  # Update the progress bar

    print(output)  # Print the captured output after all commands are executed

print("Configuration update completed.")
