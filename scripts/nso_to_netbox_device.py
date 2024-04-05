# This scripts queries NSO to see if it has knowledge of any devices that Netbox is unaware of.
# If it sees a devices that does not exist in Netbox, it will add it.

import requests
import os
import csv
import urllib3
import json
import base64

# Setup and configurations
print("Loading environment variables...")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
NSO_URL = os.getenv('NSO_URL')
NSO_USERNAME = os.getenv('NSO_USERNAME')
NSO_PASSWORD = os.getenv('NSO_PASSWORD')
NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
DEVICE_TYPE_LOOKUP_CSV_PATH = './docs/device_type_lookup.csv'

headers_netbox = {
    "Authorization": f"Token {NETBOX_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def create_device_in_netbox(device, site_id, device_lookup):
    print(f"Creating device in NetBox: {device['name']}")
    device_code = device['name'].split('-')[2]  # Extract device code
    if device_code in device_lookup:
        device_role = fetch_id('dcim/device-roles', device_lookup[device_code]['DeviceRole'], 'name')
        device_type = fetch_id('dcim/device-types', device_lookup[device_code]['DeviceType'], 'model')
    else:
        print(f"No device type/role found for code: {device_code}")
        return

    device_payload = {
        "name": device['name'],
        "site": site_id,
        "device_role": device_role,
        "device_type": device_type,
        "serial": "",
    }
    device_response = requests.post(f"{NETBOX_URL}/api/dcim/devices/", headers=headers_netbox, json=device_payload, verify=False)
    if device_response.status_code in [200, 201]:
        device_id = device_response.json()["id"]
        print(f"Device {device['name']} created successfully with ID {device_id}.")
        create_management_interface_and_set_primary_ip(device_id, device['address'])

    else:
        print(f"Failed to create device {device['name']}: {device_response.text}")

def create_management_interface_and_set_primary_ip(device_id, ip_address):
    print(f"Creating 'Management' interface for device ID {device_id}...")
    
    if not ip_address.endswith('/32'):
        ip_address += '/32'
    
    # Create the Management interface
    interface_payload = {"device": device_id, "name": "Management", "type": "virtual"}
    interface_response = requests.post(f"{NETBOX_URL}/api/dcim/interfaces/", headers=headers_netbox, json=interface_payload, verify=False)
    
    if interface_response.status_code in [200, 201]:
        interface_id = interface_response.json()["id"]
        print(f"'Management' interface with ID {interface_id} created successfully.")
        
        # Create the IP address and assign it to the interface
        ip_payload = {"address": ip_address, "status": "active", "assigned_object_id": interface_id, "assigned_object_type": "dcim.interface"}
        ip_response = requests.post(f"{NETBOX_URL}/api/ipam/ip-addresses/", headers=headers_netbox, json=ip_payload, verify=False)
        
        if ip_response.status_code in [200, 201]:
            ip_id = ip_response.json()["id"]
            print(f"IP address {ip_address} created and assigned successfully.")
            
            # Set the IP address as the primary IP for the device
            device_update_payload = {"primary_ip4": ip_id}  # or "primary_ip6" for IPv6
            device_update_response = requests.patch(f"{NETBOX_URL}/api/dcim/devices/{device_id}/", headers=headers_netbox, json=device_update_payload, verify=False)
            
            if device_update_response.status_code in [200, 201, 204]:
                print(f"Primary IP set successfully for device ID {device_id}.")
            else:
                print(f"Failed to set primary IP for device ID {device_id}: {device_update_response.text}")
        else:
            print(f"Failed to create and assign IP address {ip_address}: {ip_response.text}")
    else:
        print(f"Failed to create 'Management' interface: {interface_response.text}")

def fetch_id(endpoint, search_param, search_field='name'):
    """Fetch a NetBox entity's ID based on a search field and parameter."""
    print(f"Fetching ID for '{search_param}' from {endpoint}...")
    url = f"{NETBOX_URL}/api/{endpoint}/"
    params = {search_field: search_param}
    response = requests.get(url, headers=headers_netbox, params=params, verify=False)
    if response.status_code == 200 and response.json()['count'] == 1:
        return response.json()['results'][0]['id']
    else:
        print(f"Failed to fetch ID for {search_param} from {endpoint}.")
        return None

def fetch_sites():
    """Fetch all sites from NetBox and return a dictionary mapping site slugs to their IDs."""
    site_mapping = {}
    url = f"{NETBOX_URL}/api/dcim/sites/"
    response = requests.get(url, headers=headers_netbox, verify=False)
    if response.status_code == 200:
        for site in response.json()['results']:
            site_mapping[site['slug'].upper()] = site['id']
    else:
        print("Failed to fetch sites from NetBox.")
    return site_mapping

def load_device_lookup():
    """Load the device role and type lookup from a CSV file."""
    lookup = {}
    with open(DEVICE_TYPE_LOOKUP_CSV_PATH, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            lookup[row['Code']] = {'DeviceRole': row['DeviceRole'], 'DeviceType': row['DeviceType']}
    return lookup

def fetch_netbox_devices():
    """Fetch existing devices from NetBox."""
    netbox_devices = {}
    url = f"{NETBOX_URL}/api/dcim/devices/"
    response = requests.get(url, headers=headers_netbox, verify=False)
    if response.status_code == 200:
        for device in response.json()['results']:
            netbox_devices[device['name']] = device
    else:
        print("Failed to fetch devices from NetBox.")
    return netbox_devices

def fetch_nso_devices():
    """Fetch device information from NSO using a specific query."""
    print("Fetching devices from NSO...")
    url = f"{NSO_URL}/restconf/tailf/query"
    payload = json.dumps({
        "tailf-rest-query:immediate-query": {
            "foreach": "/devices/device",
            "select": [
                {"label": "name", "expression": "name", "result-type": "string"},
                {"label": "address", "expression": "address", "result-type": "string"}
            ]
        }
    })
    headers = {
        'Content-Type': 'application/yang-data+json',
        'Accept': 'application/yang-data+json',
        'Authorization': f'Basic {base64.b64encode(f"{NSO_USERNAME}:{NSO_PASSWORD}".encode()).decode("utf-8")}'
    }

    response = requests.post(url, headers=headers, data=payload, auth=(NSO_USERNAME, NSO_PASSWORD), verify=False)
    if response.status_code == 200:
        results = response.json().get("tailf-rest-query:query-result", {}).get("result", [])
        devices = []
        for result in results:
            device = {select["label"]: select["value"] for select in result["select"]}
            devices.append(device)
        print("NSO devices fetched successfully.")
        return devices
    else:
        print(f"Failed to fetch devices from NSO: {response.text}")
        return []


def assign_ip_to_interface(device_id, interface_id, ip_address):
    # Create the IP address
    ip_payload = {
        "address": ip_address,
        "status": "active"
    }
    ip_response = requests.post(f"{NETBOX_URL}/api/ipam/ip-addresses/", headers=headers_netbox, json=ip_payload, verify=False)
    if ip_response.status_code in [200, 201]:
        print(f"IP address {ip_address} created successfully.")
        ip_id = ip_response.json()["id"]
        
        # Associate the IP address with the interface
        association_payload = {
            "assigned_object_type": "dcim.interface",
            "assigned_object_id": interface_id
        }
        association_response = requests.patch(f"{NETBOX_URL}/api/ipam/ip-addresses/{ip_id}/", headers=headers_netbox, json=association_payload, verify=False)
        if association_response.status_code in [200, 201, 204]:
            print(f"IP address {ip_address} assigned to interface ID {interface_id} successfully.")
        else:
            print(f"Failed to assign IP address {ip_address} to interface: {association_response.text}")
    else:
        print(f"Failed to create IP address {ip_address}: {ip_response.text}")

def main():
    print("Starting script...")
    device_lookup = load_device_lookup()
    site_mapping = fetch_sites()
    netbox_devices = fetch_netbox_devices()
    nso_devices = fetch_nso_devices()

    for device in nso_devices:
        if device['name'] not in netbox_devices:
            site_code = device['name'][:4].upper()
            site_id = site_mapping.get(site_code)
            if site_id:
                create_device_in_netbox(device, site_id, device_lookup)
            else:
                print(f"Site code {site_code} not found in NetBox.")
        else:
            print(f"Device {device['name']} already exists in NetBox.")

if __name__ == "__main__":
    main()