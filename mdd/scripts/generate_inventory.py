import os
import requests
import yaml

NETBOX_URL = os.environ.get('NETBOX_URL') # Was NETBOX_API
NETBOX_TOKEN = os.environ.get('NETBOX_TOKEN')

if not NETBOX_URL or not NETBOX_TOKEN:
    print("Error: NETBOX_API or NETBOX_TOKEN environment variables are not set.")
    exit(1)

headers = {'Authorization': f'Token {NETBOX_TOKEN}'}
verify_ssl = False
existing_inventory_path = '/path/to/existing/inventory.yml'  # Replace with the actual path

def get_inventory_structure(): #TODO: Compare to generate_tags
    """Generated default inventory structure"""
    return {
        'all': {
            'children': {
                'network': {
                    'children': {}
                }
            }
        }
    }

def fetch_netbox_devices():
    existing_inventory = {}

    # Make API requests to NetBox to retrieve device information
    response = requests.get(
        f'{NETBOX_URL}/api/dcim/devices/',
        headers=headers,
        verify=verify_ssl  # Disable SSL certificate validation
    )

    if response.status_code != 200:
        print(f"Error fetching devices from NetBox: {response.status_code}")
        exit(1)

    # Create an empty inventory dictionary
    inventory_data = get_inventory_structure()

    # Check for an existing inventory file in a different directory
    if os.path.exists(existing_inventory_path):
        with open(existing_inventory_path, 'r') as existing_inventory_file:
            existing_inventory = yaml.safe_load(existing_inventory_file)

    # Populate the inventory with devices based on device role
    for device in response.json()['results']:
        device_name = device['name']
        device_role = device['device_role']['slug']

        # Check if the device is not in the existing inventory
        if device_name in existing_inventory.get('all', {}).get('children', {}).get('network', {}).get('children', {}).get(device_role, {}).get('hosts', {}):
            continue

        # Check if primary_ip4 exists and is not None
        primary_ip_data = device.get('primary_ip4')
        if not primary_ip_data:
            inventory_data['all']['children']['network']['children'].setdefault(device_role, {}).setdefault('hosts', {}).setdefault(device_name, {})
            continue

        primary_ip_address = primary_ip_data.get('address') #TODO: will this ever not be there
        primary_ip = primary_ip_address.split('/')[0]  # Extract IP without the /32

        inventory_data['all']['children']['network']['children'].setdefault(device_role, {}).setdefault('hosts', {}).setdefault(device_name, {})['ansible_host'] = primary_ip

    return inventory_data

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
