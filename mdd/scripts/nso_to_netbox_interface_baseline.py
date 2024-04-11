import requests
import base64
import json
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
NSO_URL = os.getenv('NSO_URL')
NSO_USERNAME = os.getenv('NSO_USERNAME')
NSO_PASSWORD = os.getenv('NSO_PASSWORD')
NSO_API_PATH = '/restconf/data/tailf-ncs:devices/device={device_name}/live-status/tailf-ned-cisco-ios-stats:interfaces'
NETBOX_API_DEVICE_PATH = '/api/dcim/devices/'

# Headers setup
NETBOX_HEADERS = {
    "Authorization": f"Token {NETBOX_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
NSO_AUTH = base64.b64encode(f"{NSO_USERNAME}:{NSO_PASSWORD}".encode()).decode('utf-8')
NSO_HEADERS = {
    "Authorization": f"Basic {NSO_AUTH}",
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}

# Interface type mapping
interface_type_mapping = {
    "GigabitEthernet": "1000base-t",
    "TenGigabitEthernet": "10gbase-t",
    "FastEthernet": "100base-tx"
}

def get_netbox_devices():
    """Fetch devices from Netbox."""
    url = f"{NETBOX_URL}{NETBOX_API_DEVICE_PATH}"
    response = requests.get(url, headers=NETBOX_HEADERS, verify=False)
    devices = []
    if response.status_code == 200:
        data = response.json().get('results', [])
        for device in data:
            devices.append((device['name'], device['id']))
    else:
        print(f"Failed to fetch devices from Netbox: {response.status_code}")
    return devices

def get_nso_interface_data(device_name):
    """Query NSO for interface data."""
    url = f"{NSO_URL}/restconf/data/tailf-ncs:devices/device={device_name}/live-status/tailf-ned-cisco-ios-stats:interfaces"
    response = requests.get(url, headers=NSO_HEADERS, verify=False)
    if response.status_code == 200:
        return response.json().get("tailf-ned-cisco-ios-stats:interfaces", [])
    else:
        print(f"Failed to fetch interface data for {device_name} from NSO: {response.status_code}")
        return []

def update_netbox_interfaces(device_id, device_name, interfaces):
    """Update interfaces for a device in Netbox."""
    payload = []
    for interface in interfaces:
        netbox_type = interface_type_mapping.get(interface["type"], "other")
        enabled = interface["admin-status"] == "up"
        payload.append({
            "device": device_id,
            "name": interface["name"],
            "type": netbox_type,
            "enabled": enabled,
            "description": f'{interface["type"]} {interface["name"]}'  # Adjusted to use as description
        })

    if payload:
        # Assuming batch update or creation isn't directly supported; iterate through interfaces
        for interface in payload:
            post_url = f"{NETBOX_URL}/api/dcim/interfaces/"
            response = requests.post(post_url, headers=NETBOX_HEADERS, json=interface, verify=False)
            if response.status_code in [200, 201]:
                print(f"Interface {interface['name']} updated/created successfully for device {device_name}.")
            else:
                print(f"Failed to update/create interface {interface['name']} for device {device_name}: {response.text}")

def main():
    devices = get_netbox_devices()
    for device_name, device_id in devices:
        interfaces = get_nso_interface_data(device_name)
        if interfaces:
            update_netbox_interfaces(device_id, device_name, interfaces)

if __name__ == "__main__":
    main()
