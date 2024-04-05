import os
import requests
import yaml

def fetch_netbox_devices():
    # Retrieve API key and URL from environment variables
    netbox_api_url = os.environ.get('NETBOX_API')
    netbox_api_token = os.environ.get('NETBOX_TOKEN')

    if not netbox_api_url or not netbox_api_token:
        print("Error: NETBOX_API or NETBOX_TOKEN environment variables are not set.")
        exit(1)

    # Construct the API request headers
    headers = {
        'Authorization': f'Token {netbox_api_token}'
    }

    # Disable SSL certificate validation
    verify_ssl = False

    # Make API requests to NetBox to retrieve device information
    response = requests.get(
        f'{netbox_api_url}/api/dcim/devices/',
        headers=headers,
        verify=verify_ssl  # Disable SSL certificate validation
    )

    if response.status_code == 200:
        # Parse the JSON response into a Python dictionary
        device_data = response.json()

        # Create an empty inventory dictionary
        inventory_data = {
            'all': {
                'children': {
                    'network': {
                        'children': {}
                    }
                }
            }
        }

        # Check for an existing inventory file in a different directory
        existing_inventory_path = '/path/to/existing/inventory.yml'  # Replace with the actual path
        existing_inventory = {}

        if os.path.exists(existing_inventory_path):
            with open(existing_inventory_path, 'r') as existing_inventory_file:
                existing_inventory = yaml.safe_load(existing_inventory_file)

        # Populate the inventory with devices based on device role
        for device in device_data['results']:
            device_name = device['name']
            device_role = device['device_role']['slug']

            # Check if the device is not in the existing inventory
            if device_name not in existing_inventory.get('all', {}).get('children', {}).get('network', {}).get('children', {}).get(device_role, {}).get('hosts', {}):
                # Check if primary_ip4 exists and is not None
                primary_ip_data = device.get('primary_ip4')
                if primary_ip_data and primary_ip_data.get('address'):
                    primary_ip = primary_ip_data['address'].split('/')[0]  # Extract IP without the /32
                    # Create groups for each device role under the "network" group if they don't exist
                    if device_role not in inventory_data['all']['children']['network']['children']:
                        inventory_data['all']['children']['network']['children'][device_role] = {
                            'hosts': {}
                        }

                    # Add the device to its respective role group and include the ansible_host
                    inventory_data['all']['children']['network']['children'][device_role]['hosts'][device_name] = {
                        'ansible_host': primary_ip
                    }
                else:
                    # If there is no IP address available, create groups without ansible_host
                    if device_role not in inventory_data['all']['children']['network']['children']:
                        inventory_data['all']['children']['network']['children'][device_role] = {
                            'hosts': {}
                        }
                    inventory_data['all']['children']['network']['children'][device_role]['hosts'][device_name] = {}

        return inventory_data
    else:
        print(f"Error fetching data from NetBox: {response.status_code}")
        exit(1)

def write_inventory_file(inventory_data):
    # Define the inventory file path as "inventory/network.yml"
    inventory_file_path = os.path.join(os.path.dirname(__file__), '..', 'inventory', 'network.yml')

    # Write the inventory data to the inventory file in Ansible YAML format
    with open(inventory_file_path, 'w') as f:
        yaml.dump(inventory_data, f, default_flow_style=False)

def main():
    inventory_data = fetch_netbox_devices()
    write_inventory_file(inventory_data)

if __name__ == '__main__':
    main()
