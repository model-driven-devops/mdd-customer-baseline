import requests
import base64
import os
import json
import urllib3

# Disable warnings for self-signed certificates
urllib3.disable_warnings()

# Environment variables
NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
NSO_URL = os.getenv('NSO_URL')
NSO_USERNAME = os.getenv('NSO_USERNAME')
NSO_PASSWORD = os.getenv('NSO_PASSWORD')

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

def get_devices_from_netbox():
    """Fetches devices from NetBox."""
    response = requests.get(f"{NETBOX_URL}/api/dcim/devices/", headers=NETBOX_HEADERS, verify=False)
    if response.status_code == 200:
        return response.json()["results"]
    else:
        print("Failed to fetch devices from NetBox")
        return []

def get_acls_from_nso(device_name):
    """Fetches ACLs for a device from NSO."""
    response = requests.get(f"{NSO_URL}/restconf/data/tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:ip/access-list", headers=NSO_HEADERS, verify=False)
    if response.status_code == 200:
        print(f"ACLs fetched for {device_name}")
        return response.json()
    else:
        print(f"Failed to fetch ACLs for {device_name} from NSO")
        return {}

def process_and_update_acls(device_id, device_name, acls):
    """Processes NSO ACLs and updates them in NetBox."""
    acl_list = []
    
    # Process standard ACLs
    for acl in acls.get("tailf-ned-cisco-ios:access-list", {}).get("standard", {}).get("std-named-acl", []):
        acl_list.append({
            "name": acl["name"].replace(".", "_"),
            "type": "standard",
            "default_action": "deny",
            "assigned_object_id": device_id,
            "assigned_object_type": "dcim.device",
        })

    # Process extended ACLs
    for acl in acls.get("tailf-ned-cisco-ios:access-list", {}).get("extended", {}).get("ext-named-acl", []):
        acl_list.append({
            "name": acl["name"].replace(".", "_"),
            "type": "extended",
            "default_action": "deny",
            "assigned_object_id": device_id,
            "assigned_object_type": "dcim.device",
        })

    # Attempt to update each ACL in Netbox
    for acl in acl_list:
        response = requests.post(f"{NETBOX_URL}/api/plugins/access-lists/access-lists/", headers=NETBOX_HEADERS, json=[acl], verify=False)
        if response.status_code in [200, 201]:
            print(f"Successfully updated ACL '{acl['name']}' in Netbox for device {device_name}.")
        else:
            print(f"Failed to update ACL '{acl['name']}' in Netbox for device {device_name}: {response.text}")



def main():
    devices = get_devices_from_netbox()
    for device in devices:
        device_name = device["name"]
        device_id = device["id"]  # Ensure device ID is correctly retrieved
        acls = get_acls_from_nso(device_name)
        if acls:
            process_and_update_acls(device_id, device_name, acls)

if __name__ == "__main__":
    main()
