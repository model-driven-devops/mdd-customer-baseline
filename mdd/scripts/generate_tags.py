import os
import requests
import yaml
import load_env_vars

ENV_VARS = {
    "NAUTOBOT_URL" : None,
    "NAUTOBOT_TOKEN" : None
}

ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)

headers = {'Authorization': f'Token {ENV_VARS['NAUTOBOT_TOKEN']}', 'Accept': 'application/json'}
verify_ssl = False

def get_inventory_structure():
    """Returns the default inventory structure"""

    return {
        'all': {
            'vars': {
                'sites': []
            },
            'children': {
                'org': {
                    'children': {}
                }
            }
        }
    }

def fetch_netbox_devices():
    # Initialize the inventory structure with vars for sites
    inventory_data = get_inventory_structure()

    # Fetch sites from NetBox
    response = requests.get(f'{ENV_VARS['NAUTOBOT_URL']}/api/dcim/sites/?limit=1000', headers=headers, verify=verify_ssl)

    if response.status_code != 200:
        print(f"Failed to fetch sites from NetBox: {response.status_code}")
        exit(1)

    # Populate the sites list
    for site in response.json()['results']:
        inventory_data['all']['vars']['sites'].append(site['name'])

    # Fetch devices from NetBox
    response = requests.get(f'{ENV_VARS['NAUTOBOT_URL']}/api/dcim/devices/?limit=1000', headers=headers, verify=verify_ssl)

    if response.status_code != 200:
        print(f"Failed to fetch devices from NetBox: {response.status_code}")
        exit(1)

    for device in response.json()['results']:
        device_name = device['name']
        site_name = device.get('site', {}).get('name', 'undefined')
        device_tags = [tag['name'] for tag in device.get('tags', [])]

        # Add the device under the site with its tags
        inventory_data['all']['children']['org']['children'].setdefault(site_name, {}).setdefault('hosts', {}).setdefault(device_name, {})['tags'] = device_tags

    return inventory_data

def write_inventory_file(inventory_data):
    inventory_file_path = os.path.join(os.path.dirname(__file__), '..', 'inventory', 'tags.yml')

    with open(inventory_file_path, 'w') as f:
        yaml.dump(inventory_data, f, default_flow_style=False, sort_keys=False)

def main():
    inventory_data = fetch_netbox_devices()
    write_inventory_file(inventory_data)

if __name__ == '__main__':
    main()
