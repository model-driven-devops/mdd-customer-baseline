# This scripts queries NSO to see if it has knowledge of any devices that Netbox is unaware of.
# If it sees a devices that does not exist in Netbox, it will add it.

import requests
import os
import csv
import urllib3
import json
import base64
import load_env_vars
from pynetbox import api

# Setup and configurations
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENV_VARS = {
    "NSO_URL": None,
    "NSO_USERNAME": None,
    "NSO_PASSWORD": None,
    "NETBOX_URL": None,
    "NETBOX_TOKEN": None
}
ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)
DEVICE_TYPE_LOOKUP_CSV_PATH = './docs/device_type_lookup.csv'

# Initialize NetBox API
netbox = api(url=ENV_VARS['NETBOX_URL'], token=ENV_VARS['NETBOX_TOKEN'])

# headers_netbox = {
#     "Authorization": f"Token {ENV_VARS['NETBOX_TOKEN']}",
#     "Content-Type": "application/json",
#     "Accept": "application/json"
# }

# def create_device_in_netbox(device, site_id, device_lookup):
#     print(f"Creating device in NetBox: {device['name']}")

#     device_code = device['name'].split('-')[2]  # Extract device code
#     if device_code in device_lookup:
#         device_role = fetch_id('dcim/device-roles', device_lookup[device_code]['DeviceRole'], 'name')
#         device_type = fetch_id('dcim/device-types', device_lookup[device_code]['DeviceType'], 'model')
#     else:
#         print(f"No device type/role found for code: {device_code}")
#         return

#     device_payload = {
#         "name": device['name'],
#         "site": site_id,
#         "device_role": device_role,
#         "device_type": device_type,
#         "serial": "",
#     }
#     device_response = requests.post(f"{ENV_VARS['NETBOX_URL']}/api/dcim/devices/", headers=headers_netbox, json=device_payload, verify=False)

#     if device_response.status_code not in [200, 201]:
#         print(f"Failed to create device {device['name']}: {device_response.text}")
#         return

#     device_id = device_response.json()["id"]
#     print(f"Device {device['name']} created successfully with ID {device_id}.")
#     create_management_interface_and_set_primary_ip(device_id, device['address'])

def create_device_in_netbox(device, site_id, device_lookup):
    print(f"Creating device in NetBox: {device['name']}")

    device_code = device['name'].split('-')[2]  # Extract device code
    if device_code not in device_lookup:
        print(f"No device type/role found for code: {device_code}")
        return

    device_role = fetch_id(device_lookup[device_code]['DeviceRole'])
    device_type = fetch_id(device_lookup[device_code]['DeviceType'])

    device_payload = {
        "name": device['name'],
        "site": site_id,
        "device_role": device_role,
        "device_type": device_type,
        "serial": "",
    }

    try:
        device_id = netbox.dcim.devices.create(**device_payload)['id']
        print(f"Device {device['name']} created successfully with ID {device_id}.")
        create_management_interface_and_set_primary_ip(device_id, device['address'])
    except Exception as e:
        print(f"Failed to create device {device['name']}: {e}")

# def create_management_interface_and_set_primary_ip(device_id, ip_address):
#     print(f"Creating 'Management' interface for device ID {device_id}...")

#     if not ip_address.endswith('/32'):
#         ip_address += '/32'

#     # Create the Management interface
#     interface_payload = {"device": device_id, "name": "Management", "type": "virtual"}
#     interface_response = requests.post(f"{ENV_VARS['NETBOX_URL']}/api/dcim/interfaces/", headers=headers_netbox, json=interface_payload, verify=False)

#     if interface_response.status_code not in [200, 201]:
#         print(f"Failed to create 'Management' interface: {interface_response.text}")
#         return

#     interface_id = interface_response.json()["id"]
#     print(f"'Management' interface with ID {interface_id} created successfully.")

#     # Create the IP address and assign it to the interface
#     ip_payload = {"address": ip_address, "status": "active", "assigned_object_id": interface_id, "assigned_object_type": "dcim.interface"}
#     ip_response = requests.post(f"{ENV_VARS['NETBOX_URL']}/api/ipam/ip-addresses/", headers=headers_netbox, json=ip_payload, verify=False)

#     if ip_response.status_code not in [200, 201]:
#         print(f"Failed to create and assign IP address {ip_address}: {ip_response.text}")
#         return

#     ip_id = ip_response.json()["id"]
#     print(f"IP address {ip_address} created and assigned successfully.")

#     # Set the IP address as the primary IP for the device
#     device_update_payload = {"primary_ip4": ip_id}  # or "primary_ip6" for IPv6
#     device_update_response = requests.patch(f"{ENV_VARS['NETBOX_URL']}/api/dcim/devices/{device_id}/", headers=headers_netbox, json=device_update_payload, verify=False)

#     if device_update_response.status_code in [200, 201, 204]:
#         print(f"Primary IP set successfully for device ID {device_id}.")
#     else:
#         print(f"Failed to set primary IP for device ID {device_id}: {device_update_response.text}")

def create_management_interface_and_set_primary_ip(device_id, ip_address):
    print(f"Creating 'Management' interface for device ID {device_id}...")

    if not ip_address.endswith('/32'):
        ip_address += '/32'

    # Create the Management interface
    interface_payload = {"device": device_id, "name": "Management", "type": "virtual"}
    try:
        interface_id = netbox.dcim.interfaces.create(**interface_payload)['id']
        print(f"'Management' interface with ID {interface_id} created successfully.")
    except Exception as e:
        print(f"Failed to create 'Management' interface: {e}")
        return

    # Create the IP address and assign it to the interface
    ip_payload = {"address": ip_address, "status": "active", "assigned_object_id": interface_id, "assigned_object_type": "dcim.interface"}
    try:
        ip_id = netbox.ipam.ip_addresses.create(**ip_payload)['id']
        print(f"IP address {ip_address} created and assigned successfully.")
    except Exception as e:
        print(f"Failed to create and assign IP address {ip_address}: {e}")
        return

    # Set the IP address as the primary IP for the device
    try:
        netbox.dcim.devices.update(device_id, primary_ip4=ip_id)
        print(f"Primary IP set successfully for device ID {device_id}.")
    except Exception as e:
        print(f"Failed to set primary IP for device ID {device_id}: {e}")

# def fetch_id(endpoint, search_param, search_field='name'):
#     """Fetch a NetBox entity's ID based on a search field and parameter."""

#     print(f"Fetching ID for '{search_param}' from {endpoint}...")
#     url = f"{ENV_VARS['NETBOX_URL']}/api/{endpoint}/"
#     params = {search_field: search_param}
#     response = requests.get(url, headers=headers_netbox, params=params, verify=False)

#     data = response.json()

#     if response.status_code != 200 or data['count'] != 1:
#         print(f"Failed to fetch ID for {search_param} from {endpoint}.")
#         return None

#     return data['results'][0]['id']
def fetch_id(endpoint, search_param, search_field='name'):
    """Fetch a NetBox entity's ID based on a search field and parameter."""
    try:
        objects = getattr(netbox, endpoint).filter(**{search_field: search_param})
        if len(objects) == 1:
            return objects[0].id
        else:
            print(f"Failed to fetch ID for {search_param} from {endpoint}.")
            return None
    except Exception as e:
        print(f"Failed to fetch ID for {search_param} from {endpoint}: {e}")
        return None

# def fetch_sites():
#     """Fetch all sites from NetBox and return a dictionary mapping site slugs to their IDs."""

#     site_mapping = {}
#     url = f"{ENV_VARS['NETBOX_URL']}/api/dcim/sites/"
#     response = requests.get(url, headers=headers_netbox, verify=False)

#     if response.status_code != 200:
#         print("Failed to fetch sites from NetBox.")
#         return {}

#     for site in response.json()['results']:
#         site_mapping[site['slug'].upper()] = site['id']
#     return site_mapping

def fetch_sites():
    """Fetch all sites from NetBox and return a dictionary mapping site slugs to their IDs."""
    try:
        sites = netbox.dcim.sites.all()
        return {site.slug.upper(): site.id for site in sites}
    except Exception as e:
        print(f"Failed to fetch sites from NetBox: {e}")
        return {}

def load_device_lookup():
    """Load the device role and type lookup from a CSV file."""

    lookup = {}
    with open(DEVICE_TYPE_LOOKUP_CSV_PATH, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            lookup[row['Code']] = {'DeviceRole': row['DeviceRole'], 'DeviceType': row['DeviceType']}
    return lookup

# def fetch_netbox_devices():
#     """Fetch existing devices from NetBox."""

#     netbox_devices = {}
#     url = f"{ENV_VARS['NETBOX_URL']}/api/dcim/devices/"
#     response = requests.get(url, headers=headers_netbox, verify=False)

#     if response.status_code == 200:
#         for device in response.json()['results']:
#             netbox_devices[device['name']] = device
#     else:
#         print("Failed to fetch devices from NetBox.")
#     return netbox_devices

def fetch_netbox_devices():
    """Fetch existing devices from NetBox."""
    try:
        devices = netbox.dcim.devices.all()
        return {device.name: device for device in devices}
    except Exception as e:
        print(f"Failed to fetch devices from NetBox: {e}")
        return {}

def fetch_nso_devices():
    """Fetch device information from NSO using a specific query."""

    print("Fetching devices from NSO...")

    devices = []
    url = f"{ENV_VARS['NSO_URL']}/restconf/tailf/query"
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
        'Authorization': f'Basic {base64.b64encode(f"{ENV_VARS['NSO_USERNAME']}:{ENV_VARS['NSO_PASSWORD']}".encode()).decode("utf-8")}'
    }

    response = requests.post(url, headers=headers, data=payload, auth=(ENV_VARS["NSO_USERNAME"], ENV_VARS["NSO_PASSWORD"]), verify=False)

    if response.status_code != 200:
        print(f"Failed to fetch devices from NSO: {response.text}")
        return []

    results = response.json().get("tailf-rest-query:query-result", {}).get("result", [])

    for result in results:
        device = {select["label"]: select["value"] for select in result["select"]}
        devices.append(device)
    print("NSO devices fetched successfully.")
    return devices

# def assign_ip_to_interface(device_id, interface_id, ip_address):

#     # Create the IP address
#     ip_payload = {
#         "address": ip_address,
#         "status": "active"
#     }
#     ip_response = requests.post(f"{ENV_VARS['NETBOX_URL']}/api/ipam/ip-addresses/", headers=headers_netbox, json=ip_payload, verify=False)

#     if ip_response.status_code not in [200, 201]:
#         print(f"Failed to create IP address {ip_address}: {ip_response.text}")
#         return

#     print(f"IP address {ip_address} created successfully.")
#     ip_id = ip_response.json()["id"]

#     # Associate the IP address with the interface
#     association_payload = {
#         "assigned_object_type": "dcim.interface",
#         "assigned_object_id": interface_id
#     }
#     association_response = requests.patch(f"{ENV_VARS['NETBOX_URL']}/api/ipam/ip-addresses/{ip_id}/", headers=headers_netbox, json=association_payload, verify=False)

#     if association_response.status_code in [200, 201, 204]:
#         print(f"IP address {ip_address} assigned to interface ID {interface_id} successfully.")
#     else:
#         print(f"Failed to assign IP address {ip_address} to interface: {association_response.text}")

def assign_ip_to_interface(device_id, interface_name, ip_address):
    try:
        device = netbox.dcim.devices.get(device_id)
        interface = device.interfaces.get(name=interface_name)
        interface_id = interface.id

        ip_data = {
            "address": ip_address,
            "status": "active",
            "interface": interface_id
        }
        ip = netbox.ipam.ip_addresses.create(**ip_data)

        print(f"IP address {ip.address} assigned to interface {interface.name} successfully.")
    except Exception as e:
        print(f"Failed to assign IP address {ip_address} to interface {interface_name}: {e}")

def main():
    print("Starting script...")
    device_lookup = load_device_lookup()
    site_mapping = fetch_sites()
    netbox_devices = fetch_netbox_devices()
    nso_devices = fetch_nso_devices()

    for device in nso_devices:
        if device['name'] in netbox_devices:
            print(f"Device {device['name']} already exists in NetBox.")
            continue

        site_code = device['name'][:4].upper()
        site_id = site_mapping.get(site_code)

        if site_id:
            create_device_in_netbox(device, site_id, device_lookup)
        else:
            print(f"Site code {site_code} not found in NetBox.")

if __name__ == "__main__":
    main()