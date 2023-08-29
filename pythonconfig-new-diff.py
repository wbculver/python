from netmiko import ConnectHandler
from tqdm import tqdm  # Import tqdm for the progress bar
from datetime import datetime

# Prompt user for device credentials
device_username = input("Enter the username: ")
device_password = input("Enter the password: ")
device_type = "cisco_ios"

# Read the list of device IPs from the host file
host_file_path = "hostfile.txt"
with open(host_file_path, "r") as host_file:
    device_ips = host_file.read().splitlines()

for device_ip in device_ips:
    # Read the changes for this device from its respective change file
    change_file_path = f"base-config{device_ip}.txt"
    with open(change_file_path, "r") as change_file:
        new_changes_to_apply = change_file.readlines()

    # Filter out lines starting with "#" and strip whitespace
    new_changes_to_apply = [line.strip() for line in new_changes_to_apply if not line.startswith("#")]

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
        print(f"Downloading the latest running configuration from {device_ip}...")

        # Download the running configuration
        running_config = net_connect.send_command("show running-config")

        # Save the running configuration to a file
        running_config_file_path = f"running_config_{device_ip}.txt"
        with open(running_config_file_path, "w") as f:
            f.write(running_config)

        print(f"Running configuration from {device_ip} saved to:", running_config_file_path)

# Generate a unique checkpoint ID using current date and username
        checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d%H%M%S')}_{device_username}"

        # Create a checkpoint on the device
        checkpoint_command = f"checkpoint {checkpoint_id}"
        output = net_connect.send_command_timing(checkpoint_command)

        print(f"Applying configuration changes to {device_ip}...")

        # Apply the changes from the filtered change list
        config_commands = [
            "configure terminal",
            *new_changes_to_apply,  # Spread the filtered changes into the list
            "end"
        ]

        output = ""
        with tqdm(total=len(config_commands), desc=f"Progress for {device_ip}", unit="step") as pbar:
            for cmd in config_commands:
                print(f"Sending command: {cmd}")  # Print the command being sent
                output += net_connect.send_command_timing(cmd + "\n")
                pbar.update(1)  # Update the progress bar

        print(output)  # Print the captured output after all commands are executed

    print(f"Configuration update for {device_ip} completed.")
