import requests
import os
import json
import urllib3
from base64 import b64encode

# Disable warnings from unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Environment variables
NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
NSO_URL = os.getenv('NSO_URL')
NSO_USERNAME = os.getenv('NSO_USERNAME')
NSO_PASSWORD = os.getenv('NSO_PASSWORD')

# Authorization headers
netbox_headers = {
    'Authorization': f'Token {NETBOX_TOKEN}',
    'Content-Type': 'application/json'
}
nso_auth = b64encode(f'{NSO_USERNAME}:{NSO_PASSWORD}'.encode()).decode()
nso_headers = {
    'Authorization': f'Basic {nso_auth}',
    'Accept': 'application/yang-data+json',
    'Content-Type': 'application/yang-data+json',
}

def fetch_interfaces_with_graphql(devices):
    interface_id_mapping = {}
    for device_name in devices.keys():
        print(f"Fetching interface IDs for device {device_name} using GraphQL...")
        # Updated to match your working payload structure
        payload = json.dumps({
            "query": f"""{{
                device_list(name: \"{device_name}\") {{
                    id
                    interfaces {{
                        id
                        name
                    }}
                }}
            }}"""
        })
        headers = {
            'Authorization': f'Token {NETBOX_TOKEN}',
            'Content-Type': 'application/json'
        }
        response = requests.post(f"{NETBOX_URL}/graphql/", headers=headers, data=payload, verify=False)
        if response.status_code == 200:
            try:
                # Processing the response to extract the interface data
                interfaces = response.json().get('data', {}).get('device_list', [])[0].get('interfaces', [])
                print(f"Successfully fetched interfaces for device {device_name}. Data: {interfaces}")
                
                for interface in interfaces:
                    interface_id_mapping[(device_name, interface['name'])] = interface['id']
            except (KeyError, TypeError, IndexError) as e:
                print(f"Error processing GraphQL response for device {device_name}: {e}")
        else:
            print(f"Failed to fetch interfaces for device {device_name}. Status Code: {response.status_code}, Response: {response.text}")

    return interface_id_mapping


def get_netbox_devices():
    print("Fetching devices from Netbox...")
    response = requests.get(f"{NETBOX_URL}/api/dcim/devices/", headers=netbox_headers, verify=False)
    if response.status_code == 200:
        devices = response.json()['results']
        print(f"Found {len(devices)} devices in Netbox.")
        return {device['name']: device['id'] for device in devices}
    else:
        print("Error fetching devices from Netbox.")
        return {}

def get_cdp_info(device_name):
    print(f"Fetching CDP information for {device_name} from NSO...")
    cdp_neighbors = []
    response = requests.get(f"{NSO_URL}/restconf/data/tailf-ncs:devices/device={device_name}/live-status/tailf-ned-cisco-ios-stats:cdp", headers=nso_headers, verify=False)
    if response.status_code == 200:
        try:
            cdp_data = response.json()['tailf-ned-cisco-ios-stats:cdp']['neighbors']
            # Confirm the structure of the first neighbor (if any)
            for neighbor in cdp_data:
                cdp_neighbors.append({
                    'local_interface': neighbor['local-interface'],
                    'neighbor_device': neighbor['device-id'],
                    'neighbor_interface': neighbor['port-id']
                })
            print(f"Found {len(cdp_neighbors)} CDP neighbors for {device_name}.")
            return cdp_neighbors
        except KeyError as e:
            print(f"Error processing NSO CDP data for {device_name}: {e}")
            return []
    else:
        print(f"Error fetching CDP info for {device_name} from NSO. Status Code: {response.status_code}, Response: {response.text}")
        return []


def create_or_update_cable(a_device_name, a_interface_name, b_device_name, b_interface_name, devices, interface_id_mapping):
    a_device_id = devices.get(a_device_name)
    b_device_id = devices.get(b_device_name.split('.')[0])  # Removing domain part if present

    # Fetching interface IDs from the mapping
    a_interface_id = interface_id_mapping.get((a_device_name, a_interface_name))
    b_interface_id = interface_id_mapping.get((b_device_name, b_interface_name))

    if a_interface_id is not None:
        a_interface_id = int(a_interface_id)
    if b_interface_id is not None:
        b_interface_id = int(b_interface_id)

    if a_interface_id is None or b_interface_id is None:
        print(f"Could not find interface IDs for {a_interface_name} on {a_device_name} or {b_interface_name} on {b_device_name}. Skipping.")
        return

    payload = {
        "type": "cat5",
        "a_terminations": [
          {
            "object_type": "dcim.interface",
            "object_id": a_interface_id
          }
        ],
        "b_terminations": [
          {
            "object_type": "dcim.interface",
            "object_id": b_interface_id
          }
        ],
      "status": "connected"
    }

    print(f"Payload being sent to Netbox for device {a_device_name} and interface {a_interface_name}: {json.dumps(payload, indent=2)}")
    response = requests.post(f'{NETBOX_URL}/api/dcim/cables/', headers=netbox_headers, json=payload, verify=False)
    if response.status_code in [200, 201]:
        print(f'Cable created successfully between {a_device_name} ({a_interface_name}) and {b_device_name} ({b_interface_name}).')
    else:
        print(f'Failed to create cable between {a_device_name} ({a_interface_name}) and {b_device_name} ({b_interface_name}): {response.text}')

def main():
    devices = get_netbox_devices()
    interface_id_mapping = fetch_interfaces_with_graphql(devices)  # Fetch interface IDs for all devices
    for device_name in devices.keys():
        cdp_neighbors = get_cdp_info(device_name)
        for neighbor in cdp_neighbors:
            print("Current neighbor data being processed:", neighbor)
            neighbor_device_without_domain = neighbor['neighbor_device'].split('.')[0]
            create_or_update_cable(
              device_name,
              neighbor['local_interface'],  
              neighbor_device_without_domain,  
              neighbor['neighbor_interface'], 
              devices,
              interface_id_mapping
    )

if __name__ == '__main__':
    main()
