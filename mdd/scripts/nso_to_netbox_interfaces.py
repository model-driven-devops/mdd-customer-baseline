import requests
import os
import json
import urllib3
import load_env_vars

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENV_VARS = {
    "NSO_URL": None,
    "NSO_USERNAME": None,
    "NSO_PASSWORD": None,
    "NETBOX_URL": None,
    "NETBOX_TOKEN": None
}

ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)

# NetBox headers for API requests
netbox_headers = {
    "Authorization": f"Token {ENV_VARS["NETBOX_TOKEN"]}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_netbox_devices():
    """Fetch all devices from NetBox."""

    print("Fetching devices from NetBox...")

    url = f"{ENV_VARS["NETBOX_URL"]}/api/dcim/devices/"
    response = requests.get(url, headers=netbox_headers, verify=False)

    if response.status_code != 200:
        print("Failed to fetch devices from NetBox.")
        return []

    print("Devices successfully fetched from NetBox.")
    return response.json()['results']

def get_nso_interfaces(device_name):
    """Fetch interfaces for a specific device from NSO."""

    print(f"Fetching interfaces for {device_name} from NSO...")

    url = f"{ENV_VARS['NSO_URL']}/restconf/data/tailf-ncs:devices/device={device_name}/live-status/tailf-ned-cisco-ios-stats:interfaces"
    response = requests.get(url, auth=(ENV_VARS['NSO_USERNAME'], ENV_VARS['NSO_PASSWORD']), headers={"Accept": "application/yang-data+json"}, verify=False)

    if response.status_code != 200:
        print(f"Failed to fetch interfaces for {device_name} from NSO.")
        return []

    print(f"Interfaces successfully fetched for {device_name} from NSO.")
    return response.json().get('tailf-ned-cisco-ios-stats:interfaces', [])


def type_translation(nso_type):
    """Translate NSO interface type to NetBox interface type."""

    translation_table = {
        "GigabitEthernet": "1000Base-T",
        "TenGigabitEthernet": "10GBase-T",
        "FastEthernet": "100Base-T"
    }
    return translation_table.get(nso_type, "Other")  # Fallback to 'Other' if type not found

def add_interface_to_device(device_id, interface):
    """Add an interface to a device in NetBox."""

    print(f"Adding interface {interface['name']} to device ID {device_id} in NetBox...")

    data = {
        "device": device_id,
        "name": f"{interface['type']} {interface['name']}",
        "type": "other",  # Simplification, real logic needed based on actual types
        "enabled": interface['admin-status'] == 'up',
        "mac_address": interface.get('mac-address', ''),
        # Additional fields as necessary
    }
    url = f"{ENV_VARS["NETBOX_URL"]}/api/dcim/interfaces/"
    response = requests.post(url, headers=netbox_headers, json=data, verify=False)

    if response.status_code not in [200, 201]:
        print(f"Failed to add interface {interface['name']} to device ID {device_id} in NetBox: {response.text}")
        return None

    print(f"Interface {interface['name']} added to device ID {device_id} in NetBox.")
    return response.json()['id']  # Return the new interface's ID for further use

def main():
    devices = get_netbox_devices()
    for device in devices:
        device_name = device['name']
        interfaces = get_nso_interfaces(device_name)
        for interface in interfaces:
            # Simplified example, assumes 'type' and 'admin-status' are present in the NSO data
            if 'type' in interface and 'admin-status' in interface:
                interface_id = add_interface_to_device(device['id'], interface)
                # Example logic for handling IP addresses or other details would go here
            else:
                print(f"Missing 'type' or 'admin-status' for an interface on {device_name}, skipping.")

if __name__ == "__main__":
    main()
