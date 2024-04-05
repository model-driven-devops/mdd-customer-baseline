import requests
import os
import json
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Environment setup
NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
NSO_URL = os.getenv('NSO_URL')
NSO_USERNAME = os.getenv('NSO_USERNAME')
NSO_PASSWORD = os.getenv('NSO_PASSWORD')
CISCO_MANUFACTURER_ID = '2'

netbox_headers = {
    "Authorization": f"Token {NETBOX_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_netbox_devices():
    """Fetch all devices from NetBox."""
    url = f"{NETBOX_URL}/api/dcim/devices/"
    response = requests.get(url, headers=netbox_headers, verify=False)
    return response.json()['results'] if response.status_code == 200 else []

def get_nso_inventory(device_name):
    """Fetch inventory for a specific device from NSO."""
    url = f"{NSO_URL}/restconf/data/tailf-ncs:devices/device={device_name}/live-status/tailf-ned-cisco-ios-stats:inventory"
    response = requests.get(url, auth=(NSO_USERNAME, NSO_PASSWORD), headers={"Accept": "application/yang-data+json"}, verify=False)
    return response.json().get('tailf-ned-cisco-ios-stats:inventory', []) if response.status_code == 200 else []

def fetch_existing_serial_numbers(device_id):
    """Fetch existing serial numbers of inventory items for a given device."""
    url = f"{NETBOX_URL}/api/dcim/inventory-items/?device_id={device_id}"
    response = requests.get(url, headers=netbox_headers, verify=False)
    if response.status_code == 200:
        return [item['serial'] for item in response.json()['results'] if item['serial']]
    return []

def add_netbox_inventory_item(device_id, device_name, inventory_item, existing_serials):
    """Add an inventory item to a NetBox device, skipping duplicates and items without 'pid'."""
    pid = inventory_item.get('pid')
    sn = inventory_item.get('sn')

    if not pid or sn in existing_serials or pid == device_name:
        return  # Skip if pid is missing, serial is duplicate, or pid matches device name

    data = {
        "device": device_id,
        "name": pid,
        "label": pid,
        "description": inventory_item.get('descr', ''),
        "manufacturer": CISCO_MANUFACTURER_ID,  # Ensure this ID exists in NetBox
        "part_id": pid,
        "serial": sn,
    }
    response = requests.post(f"{NETBOX_URL}/api/dcim/inventory-items/", headers=netbox_headers, json=data, verify=False)
    if response.status_code in [200, 201]:
        print(f"Inventory item {pid} added to device {device_id}.")
    else:
        print(f"Failed to add inventory item {pid} to device {device_id}: {response.text}")

def main():
    devices = get_netbox_devices()
    for device in devices:
        device_name = device['name']
        inventory_items = get_nso_inventory(device_name)
        existing_serials = fetch_existing_serial_numbers(device['id'])
        for item in inventory_items:
            add_netbox_inventory_item(device['id'], device_name, item, existing_serials)

if __name__ == "__main__":
    main()
