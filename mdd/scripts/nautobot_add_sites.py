import csv
import requests
import os

# Nautobot details
NAUTOBOT_URL = os.environ.get("NAUTOBOT_URL")
NAUTOBOT_TOKEN = os.environ.get("NAUTOBOT_TOKEN")
HEADERS = {
    'Authorization': f'Token {NAUTOBOT_TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

# Disable SSL Warnings (for self-signed certificates)
requests.packages.urllib3.disable_warnings()

def create_site(site):
    url = f"{NAUTOBOT_URL}/dcim/sites/"
    response = requests.post(url, headers=HEADERS, json=site, verify=False)

    if response.status_code == 201:
        print(f"Site '{site['name']}' created successfully.")
    else:
        print(f"Failed to create site '{site['name']}': {response.text}")

def create_device(device):
    url = f"{NAUTOBOT_URL}/dcim/devices/"
    response = requests.post(url, headers=HEADERS, json=device, verify=False)

    if response.status_code == 201:
        print(f"Device '{device['name']}' created successfully.")
        return response.json()['id']  # Return device ID for further use

    print(f"Failed to create device '{device['name']}': {response.text}")

def create_interface(device_id, interface):
    url = f"{NAUTOBOT_URL}/dcim/interfaces/"
    interface['device'] = device_id

    response = requests.post(url, headers=HEADERS, json=interface, verify=False)

    if response.status_code == 201:
        print(f"Interface '{interface['name']}' created successfully.")
        return response.json()['id']

    print(f"Failed to create interface '{interface['name']}': {response.text}")

def assign_ip_to_interface(interface_id, ip):
    url = f"{NAUTOBOT_URL}/ipam/ip-addresses/"
    ip_data = {
        "address": ip,
        "assigned_object_type": "dcim.interface",
        "assigned_object_id": interface_id
    }

    response = requests.post(url, headers=HEADERS, json=ip_data, verify=False)

    if response.status_code == 201:
        print(f"IP Address '{ip}' assigned successfully.")
    else:
        print(f"Failed to assign IP Address '{ip}': {response.text}")

# Import Sites from CSV
with open('docs/netbox_sites.csv', mode='r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        site = {
            "name": row['Name'],
            "slug": row['Slug'],
            "status": "active" if row['Active'] == "Active" else "inactive",
            "region": None,  # Adjust this if you are using regions
            "description": row['Comments'],
            # Include more fields as needed
        }
        create_site(site)

# Import Devices from CSV
with open('docs/netbox_devices.csv', mode='r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        device = {
            "name": row['Name'],
            "device_type": None,  # Specify device type ID
            "device_role": None,  # Specify device role ID
            "site": row['Name'][:4].upper(),  # Match site by first four letters of device name
            "status": "active" if row['Status'] == "Active" else "planned",
            # Include more fields as needed
        }
        device_id = create_device(device)
        if device_id and row.get('IP Address'):
            interface_id = create_interface(device_id, {"name": "Management", "type": "virtual"})
            if interface_id:
                assign_ip_to_interface(interface_id, row['IP Address'])
