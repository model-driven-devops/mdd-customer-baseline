import os
import requests
import ipaddress
import base64
import urllib3
urllib3.disable_warnings()

# Environment variables
NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
NSO_URL = os.getenv('NSO_URL')
NSO_USERNAME = os.getenv('NSO_USERNAME')
NSO_PASSWORD = os.getenv('NSO_PASSWORD')

# Headers
NETBOX_HEADERS = {
    'Authorization': f'Token {NETBOX_TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

NSO_HEADERS = {
    'Authorization': f'Basic {base64.b64encode(f"{NSO_USERNAME}:{NSO_PASSWORD}".encode()).decode()}',
    'Accept': 'application/yang-data+json',
    'Content-Type': 'application/yang-data+json',
}

def get_devices_from_netbox():
    """Fetches devices from NetBox."""
    response = requests.get(f"{NETBOX_URL}/api/dcim/devices/", headers=NETBOX_HEADERS, verify=False)
    if response.status_code == 200:
        return response.json().get('results', [])
    print("Failed to fetch devices from NetBox")
    return []

def get_acls_from_nso(device_name):
    """Fetch ACL rules for a given device from NSO."""
    url = f"{NSO_URL}/restconf/data/tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:ip/access-list"
    response = requests.get(url, headers=NSO_HEADERS, verify=False)
    if response.status_code == 200:
        return response.json().get('tailf-ned-cisco-ios:access-list', {})
    else:
        print(f"Failed to fetch ACLs for {device_name} from NSO: Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def calculate_cidr(rule):
    """Converts rule to CIDR notation for extended ACLs."""
    parts = rule.split()
    if len(parts) < 4:
        return None  # Skip rules without IP address

    ip = parts[3]
    if len(parts) >= 6 and parts[4] == '0.0.0.255':
        # Handling wildcard mask
        return f"{ip}/{ipaddress.IPv4Network(f'0.0.0.0/{parts[4]}').prefixlen}"
    elif len(parts) >= 5 and parts[4] == 'host':
        return f"{parts[5]}/32"  # Treat 'host' as /32 subnet mask
    else:
        return f"{ip}/32"

def add_prefix_to_netbox(prefix, description):
    """Adds a given prefix to NetBox."""
    data = {
        "prefix": prefix,
        "status": "active",
        "description": description
    }
    response = requests.post(f"{NETBOX_URL}/api/ipam/prefixes/", headers=NETBOX_HEADERS, json=data, verify=False)
    if response.status_code in [200, 201]:
        print(f"Successfully added prefix {prefix} to NetBox.")
    else:
        print(f"Failed to add prefix {prefix} to NetBox: {response.text}")

def process_and_add_prefixes(device_name, acls):
    """Process ACL rules and add prefixes to NetBox."""
    # Process standard ACLs
    for acl in acls.get("standard", {}).get("std-named-acl", []):
        acl_name = acl.get("name")
        rules = acl.get("std-access-list-rule", [])
        for rule in rules:
            rule_text = rule.get("rule")
            cidr = calculate_cidr(rule_text)
            if cidr:
                add_prefix_to_netbox(cidr, f"{acl_name}")

    # Process extended ACLs
    for acl in acls.get("extended", {}).get("ext-named-acl", []):
        acl_name = acl.get("name")
        rules = acl.get("ext-access-list-rule", [])
        for rule in rules:
            rule_text = rule.get("rule")
            cidr = calculate_cidr(rule_text)
            if cidr:
                add_prefix_to_netbox(cidr, f"{acl_name}")

def main():
    devices = get_devices_from_netbox()
    for device in devices:
        device_name = device['name']
        print(f"Fetching ACLs for device: {device_name}")
        acls = get_acls_from_nso(device_name)
        if acls:
            print(f"Acls fetched for {device_name}: {acls}")
            process_and_add_prefixes(device_name, acls)
        else:
            print(f"Skipping device {device_name} due to ACL fetch failure.")

if __name__ == "__main__":
    main()
