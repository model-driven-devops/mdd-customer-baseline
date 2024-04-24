import csv
import os
from pynetbox import api
import load_env_vars

ENV_VARS = {
    "NETBOX_URL": None,
    "NETBOX_TOKEN": None
}
DEVICES_CSV_FILE_PATH = './docs/netbox_devices.csv'
DEVICE_TYPE_LOOKUP_CSV_PATH = './docs/device_type_lookup.csv'

ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)

# Initialize NetBox API
netbox = api(url=ENV_VARS['NETBOX_URL'], token=ENV_VARS['NETBOX_TOKEN'])

def fetch_id(endpoint, search_param, search_field='name'):
    try:
        objects = getattr(netbox.dcim, endpoint).filter(**{search_field: search_param})
        return objects[0].id if objects else None
    except Exception as e:
        print(f"Error fetching ID for {search_param} from {endpoint}: {e}")
        return None

def fetch_sites():
    return {site.slug.upper(): site.id for site in netbox.dcim.sites.all()}

def add_management_interface_and_ip(device, ip_address):
    try:
        interface = device.interfaces.create(name="Management", type="virtual", enabled=True)
        interface.ip_addresses.create(address=ip_address)
        device.primary_ip4 = interface.primary_ip.id
        device.save()
        print(f"Management interface added to device {device.name} with IP {ip_address}.")
    except Exception as e:
        print(f"Error adding management interface to device {device.name}: {e}")

def create_device(row, site_mapping, device_lookup):
    site_id = site_mapping.get(row['Name'][:4].upper(), site_mapping.get('DEFAULT'))
    device_code = row['Name'][9:11]
    lookup = device_lookup.get(device_code, {})
    device_role_id = fetch_id('device_roles', lookup.get('DeviceRole'))
    device_type_id = fetch_id('device_types', lookup.get('DeviceType'), 'model')

    if not all([site_id, device_role_id, device_type_id]):
        print(f"Skipping device creation for {row['Name']} due to missing required IDs.")
        return

    try:
        device = netbox.dcim.devices.create(
            name=row['Name'],
            site=site_id,
            device_role=device_role_id,
            device_type=device_type_id,
            serial=row.get('Serial number', '')
        )
        print(f"Device '{row['Name']}' created successfully.")
        add_management_interface_and_ip(device, row.get('IP Address', ''))
    except Exception as e:
        print(f"Failed to create device '{row['Name']}': {e}")

def main():
    print("Script started.")
    site_mapping = fetch_sites()
    print(f"Loaded {len(site_mapping)} sites.")

    device_lookup = {row['Code']: {'DeviceRole': row['DeviceRole'], 'DeviceType': row['DeviceType']} for row in csv.DictReader(open(DEVICE_TYPE_LOOKUP_CSV_PATH))}
    print(f"Loaded device lookup with codes: {list(device_lookup.keys())}")

    for row in csv.DictReader(open(DEVICES_CSV_FILE_PATH)):
        print(f"Processing device {row['Name']}...")
        create_device(row, site_mapping, device_lookup)

if __name__ == "__main__":
    main()


# def fetch_id(endpoint, search_param, search_field='name'):
#     url = f"{ENV_VARS['NETBOX_URL']}/api/{endpoint}/"
#     params = {search_field: search_param}

#     response = requests.get(url, headers=headers, params=params, verify=False)

#     if response.status_code != 200:
#         print(f"Error fetching ID for {search_param} from {endpoint}.")
#         return None

#     if response.json()['count'] == 1:
#         return response.json()['results'][0]['id']

#     if response.json()['count'] > 1:
#         print(f"Multiple matches found for {search_param} from {endpoint}, using the first one.")
#         return response.json()['results'][0]['id']

#     return None # count == 0

# def load_device_lookup():
#     lookup = {}
#     with open(DEVICE_TYPE_LOOKUP_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             lookup[row['Code']] = {'DeviceRole': row['DeviceRole'], 'DeviceType': row['DeviceType']}
#     return lookup

# def fetch_sites():
#     site_mapping = {}
#     url = f"{ENV_VARS['NETBOX_URL']}/api/dcim/sites/"
#     response = requests.get(url, headers=headers, verify=False)

#     for site in response.json().get('results', []):
#         site_mapping[site['slug'].upper()] = site['id']

#     return site_mapping

# # def add_management_interface_and_ip(device_id, ip_address):
# #     print(f"Starting to add management interface to device ID {device_id}...")

# #     # Step 1: Create the management interface
# #     url = f"{ENV_VARS['NETBOX_URL']}/api/dcim/interfaces/"
# #     data = {"device": device_id, "name": "Management", "type": "virtual", "enabled": True}
# #     interface_response = requests.post(url, headers=headers, json=data, verify=False)

# #     if interface_response.status_code not in [200, 201]:
# #         print(f"Failed to create 'Management' interface for device ID {device_id}: {interface_response.text}")
# #         return

# #     interface_id = interface_response.json()['id']
# #     print(f"'Management' interface with ID {interface_id} created successfully.")

# #     # Step 2: Assign the IP address to the management interface
# #     ip_url = f"{ENV_VARS['NETBOX_URL']}/api/ipam/ip-addresses/"
# #     ip_data = {
# #         "address": ip_address,
# #         "assigned_object_id": interface_id,
# #         "assigned_object_type": "dcim.interface"
# #     }
# #     ip_response = requests.post(ip_url, headers=headers, json=ip_data, verify=False)

# #     if ip_response.status_code not in [200, 201]:
# #         print(f"Failed to assign IP address {ip_address} to 'Management' interface: {ip_response.text}")
# #         return

# #     print(f"IP address {ip_address} assigned successfully to 'Management' interface.")
# #     ip_id = ip_response.json()['id']

# #     # Step 3: Set the IP address as the primary IP for the device
# #     device_update_url = f"{ENV_VARS['NETBOX_URL']}/api/dcim/devices/{device_id}/"
# #     device_update_data = {
# #         "primary_ip4": ip_id
# #     }
# #     device_update_response = requests.patch(device_update_url, headers=headers, json=device_update_data, verify=False)

# #     if device_update_response.status_code in [200, 201, 204]:
# #         print(f"IP address {ip_address} set as primary IP for device ID {device_id}.")
# #     else:
# #         print(f"Failed to set IP address as primary for device ID {device_id}: {device_update_response.text}")

# def create_device(row, site_mapping, device_lookup):
#     site_prefix = row['Name'][:4].upper()
#     site_id = site_mapping.get(site_prefix, site_mapping.get('DEFAULT'))
#     device_code = row['Name'][9:11]
#     lookup = device_lookup.get(device_code, {})

#     device_role_id = fetch_id('dcim/device-roles', lookup.get('DeviceRole'), 'name')
#     device_type_id = fetch_id('dcim/device-types', lookup.get('DeviceType'), 'model')

#     if not (site_id and device_role_id and device_type_id):
#         print(f"Skipping device creation for {row['Name']} due to missing required IDs.")
#         return

#     data = {"name": row['Name'], "site": site_id, "device_role": device_role_id, "device_type": device_type_id, "serial": row.get('Serial number', '')}
#     device_response = requests.post(f"{ENV_VARS['NETBOX_URL']}/api/dcim/devices/", headers=headers, json=data, verify=False)

#     if device_response.status_code in [200, 201]:
#         print(f"Device '{row['Name']}' created successfully.")
#         device_id = device_response.json()['id']
#         add_management_interface_and_ip(device_id, row.get('IP Address', ''))
#     else:
#         print(f"Failed to create device '{row['Name']}': {device_response.text}")

# def main():
#     print("Script started.")

#     site_mapping = fetch_sites()
#     print(f"Loaded {len(site_mapping)} sites.")

#     device_lookup = load_device_lookup()
#     print(f"Loaded device lookup with codes: {list(device_lookup.keys())}")

#     with open(DEVICES_CSV_FILE_PATH, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             print(f"Processing device {row['Name']}...")
#             create_device(row, site_mapping, device_lookup)

# if __name__ == "__main__":
#     main()