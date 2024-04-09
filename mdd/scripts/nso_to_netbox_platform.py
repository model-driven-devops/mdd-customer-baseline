# This script will use the devices in Netbox and query NSO to get the software version
# serial number and model of each device. It will add the data to the device in netbox.

import requests
import os
import json
import urllib3
from netbox_class import netbox_helper

# Environment Variables
NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
NSO_URL = os.getenv('NSO_URL')
NSO_USERNAME = os.getenv('NSO_USERNAME')
NSO_PASSWORD = os.getenv('NSO_PASSWORD')

# Headers for NetBox
netbox_headers = {
    "Authorization": f"Token {NETBOX_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Disable SSL warnings for simplicity in this script
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_nso_platform_info(device_name):
    """Fetch platform information for a specific device from NSO."""
    # Corrected URL with device_name included dynamically
    url = f"https://nso.cisco.development.smit-th.com:30002/restconf/data/tailf-ncs:devices/device={device_name}/platform"

    headers = {
        'Content-Type': 'application/yang-data+json',
        'Accept': 'application/yang-data+json',
        'Authorization': 'Basic YWRtaW46YWlUaDd1c2g='  # This seems to be a base64 encoded string of 'admin:aiTh7ush'
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code != 200:
        print(f"Failed to retrieve platform information for {device_name} from NSO: {response.status_code}, {response.text}")
        return None

    platform_info = response.json().get("tailf-ncs:platform")
    if not platform_info:
        print(f"Platform information is missing for {device_name}.")
        return None

    print(json.dumps(platform_info, indent=4))  # Debug print
    return platform_info

def get_or_create_platform(name, version):
    """Ensure the platform exists in NetBox, based on the combined name and version, and return its ID."""
    platform_identifier = f"{name} {version}"
    url = f"{NETBOX_URL}/api/dcim/platforms/?name={platform_identifier}"
    response = requests.get(url, headers=netbox_headers, verify=False)

    if response.status_code != 200:
        return None # Server error?

    response = response.json()

    if response['count'] != 0: # Platform exists
        return response['results'][0]['id']

    # Platform doesn't exist - so create one
    data = {
        "name": platform_identifier,
        "slug": platform_identifier.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(".", "-")
    }
    create_response = requests.post(f"{NETBOX_URL}/api/dcim/platforms/", headers=netbox_headers, data=json.dumps(data), verify=False)

    if create_response.status_code not in [200, 201]:
        print(f"Failed to create platform {platform_identifier}: {create_response.text}")
        return None

    print(f"Successfully added platform: {platform_identifier}")
    return create_response.json()['id']

def get_or_create_device_type(model):
    """Ensure the device type exists in NetBox, based on the model from NSO, and return its ID."""

    url = f"{NETBOX_URL}/api/dcim/device-types/?model={model}"
    response = requests.get(url, headers=netbox_headers, verify=False)

    if response.status_code != 200 or response.json()['count'] > 0:
        # Device exists
        return response.json()['results'][0]['id']

    # Device type does not exist, create it
    data = {
        "model": model,
        "slug": model.lower().replace(" ", "-").replace("_", "-"),
        "manufacturer": 1  # Example manufacturer ID, adjust accordingly
    }
    create_response = requests.post(f"{NETBOX_URL}/api/dcim/device-types/", headers=netbox_headers, data=json.dumps(data), verify=False)

    if create_response.status_code not in [200, 201]:
        print(f"Failed to create device type {model}: {create_response.text}")
        return None

    return create_response.json()['id']

def update_netbox_device(device_id, platform_info):
    """Update a device in NetBox with the correct serial number, device type, and platform."""

    model = platform_info.get("model")
    serial_number = platform_info.get("serial-number")
    name = platform_info.get("name")
    version = platform_info.get("version")

    device_type_id = get_or_create_device_type(model)
    platform_id = get_or_create_platform(name, version) if name and version else None

    if not device_type_id or not platform_id:
        return

    data = {
        "serial": serial_number,
        "device_type": device_type_id,
        "platform": platform_id
    }
    url = f"{NETBOX_URL}/api/dcim/devices/{device_id}/"
    response = requests.patch(url, headers=netbox_headers, data=json.dumps(data), verify=False)

    if response.status_code in [200, 201, 204]:
        print(f"Device {device_id} updated successfully with new type, serial, and platform.")
    else:
        print(f"Failed to update device {device_id}: {response.status_code}, {response.text}")

def main():
    netbox=netbox_helper(NETBOX_URL,netbox_headers)
    for device in netbox.fetch_netbox_devices():
        device_name = device.get('name')
        platform_info = fetch_nso_platform_info(device_name)
        if platform_info:
            update_netbox_device(device.get('id'), platform_info)

if __name__ == "__main__":
    main()
