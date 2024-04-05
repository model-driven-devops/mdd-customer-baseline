import os
import requests
import yaml
import json

def fetch_netbox_devices():
    netbox_api_url = os.environ.get('NETBOX_API')
    netbox_api_token = os.environ.get('NETBOX_TOKEN')

    if not netbox_api_url or not netbox_api_token:
        print("NETBOX_API or NETBOX_TOKEN environment variables are not set.")
        exit(1)

    headers = {'Authorization': f'Token {netbox_api_token}', 'Accept': 'application/json'}
    verify_ssl = False

    # Initialize the inventory structure with vars for sites
    inventory_data = {
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

    # Fetch devices from NetBox
    response = requests.get(f'{netbox_api_url}/api/dcim/sites/?limit=1000', headers=headers, verify=verify_ssl)
    if response.status_code == 200:
        sites_data = response.json()
        # Populate the sites list
        for site in sites_data['results']:
            inventory_data['all']['vars']['sites'].append(site['name'])

    response = requests.get(f'{netbox_api_url}/api/dcim/devices/?limit=1000', headers=headers, verify=verify_ssl)
    if response.status_code == 200:
        device_data = response.json()

        for device in device_data['results']:
            device_name = device['name']
            site_name = device.get('site', {}).get('name', 'undefined')
            device_tags = [tag['name'] for tag in device.get('tags', [])]

            if site_name not in inventory_data['all']['children']['org']['children']:
                inventory_data['all']['children']['org']['children'][site_name] = {'hosts': {}}

            # Add the device under the site with its tags
            inventory_data['all']['children']['org']['children'][site_name]['hosts'][device_name] = {'tags': device_tags}
    else:
        print(f"Failed to fetch data from NetBox: {response.status_code}")
        exit(1)

    return inventory_data

def write_inventory_file(inventory_data):
    inventory_file_path = os.path.join(os.path.dirname(__file__),'..', 'inventory', 'tags.yml')

    with open(inventory_file_path, 'w') as f:
        yaml.dump(inventory_data, f, default_flow_style=False, sort_keys=False)

def main():
    inventory_data = fetch_netbox_devices()
    write_inventory_file(inventory_data)

if __name__ == '__main__':
    main()
