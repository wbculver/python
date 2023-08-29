from netmiko import ConnectHandler
from tqdm import tqdm
from datetime import datetime

def print_changes(changes):
    print("Changes to be applied:")
    for i, change in enumerate(changes, start=1):
        print(f"{i}. {change}")
    print()

def main():
    device_username = input("Enter the username: ")
    device_password = input("Enter the password: ")
    device_type = "cisco_ios"

    host_file_path = "hostfile.txt"
    with open(host_file_path, "r") as host_file:
        device_ips = host_file.read().splitlines()

    for device_ip in device_ips:
        change_file_path = f"base-config{device_ip}.txt"
        with open(change_file_path, "r") as change_file:
            new_changes_to_apply = change_file.readlines()

        new_changes_to_apply = [line.strip() for line in new_changes_to_apply if not line.startswith("#")]

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
            running_config = net_connect.send_command("show running-config")
            running_config_file_path = f"running_config_{device_ip}.txt"
            with open(running_config_file_path, "w") as f:
                f.write(running_config)
            print(f"Running configuration from {device_ip} saved to:", running_config_file_path)

            checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d%H%M%S')}_{device_username}"
            checkpoint_command = f"checkpoint {checkpoint_id}"
            output = net_connect.send_command_timing(checkpoint_command)

            print_changes(new_changes_to_apply)
            user_approval = input("Do you want to apply these changes? (yes/no): ")
            if user_approval.lower() == "yes":
                print(f"Applying configuration changes to {device_ip}...")
                config_commands = [
                    "configure terminal",
                    *new_changes_to_apply,
                    "end"
                ]
                output = ""
                with tqdm(total=len(config_commands), desc=f"Progress for {device_ip}", unit="step") as pbar:
                    for cmd in config_commands:
                        print(f"Sending command: {cmd}")
                        output += net_connect.send_command_timing(cmd + "\n")
                        pbar.update(1)
                print(output)
                print(f"Configuration update for {device_ip} completed.")
            else:
                print(f"Configuration update for {device_ip} cancelled.")

if __name__ == "__main__":
    main()
