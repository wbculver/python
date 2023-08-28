from netmiko import ConnectHandler
from tqdm import tqdm  # Import tqdm for the progress bar
from datetime import datetime

# Read the list of device IPs from the host file
host_file_path = "hostfile.txt"
with open(host_file_path, "r") as host_file:
    device_ips = host_file.read().splitlines()

for device_ip in device_ips:
    # Prompt user for device credentials
    device_username = input(f"Enter the username for {device_ip}: ")
    device_password = input(f"Enter the password for {device_ip}: ")
    device_type = "cisco_nxos"  # Use the Nexus device type

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
        print(f"Connected to {device_ip}.")

        # Generate a unique checkpoint ID using current date and username
        checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d%H%M%S')}_{device_username}"

        # Create a checkpoint on the device
        checkpoint_command = f"checkpoint file {checkpoint_id}"
        output = net_connect.send_command_timing(checkpoint_command)

        # Apply the changes from the filtered change list
        config_commands = [
            "configure terminal",
            *new_changes_to_apply,  # Spread the filtered changes into the list
            "end"
        ]

        with tqdm(total=len(config_commands), desc=f"Progress for {device_ip}", unit="step") as pbar:
            for cmd in config_commands:
                print(f"Sending command: {cmd}")  # Print the command being sent
                output += net_connect.send_command_timing(cmd + "\n")
                pbar.update(1)  # Update the progress bar

        print(output)  # Print the captured output after all commands are executed

    print(f"Configuration update for {device_ip} completed. Checkpoint ID: {checkpoint_id}")
