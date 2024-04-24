import os
import requests
import base64
import re
import urllib3
import load_env_vars
from nautobot import Nautobot
from nautobot.extras.models import Status

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENV_VARS = {
    "NSO_URL": None,
    "NSO_USERNAME": None,
    "NSO_PASSWORD": None,
    "NAUTOBOT_URL": None,
    "NAUTOBOT_TOKEN": None
}
ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)

# Initialize the Nautobot client
nautobot = Nautobot(
    url=ENV_VARS['NAUTOBOT_URL'],
    token=ENV_VARS['NAUTOBOT_TOKEN']
)

ip_pattern = re.compile(r'permit\s+(\d+\.\d+\.\d+\.\d+)(?:\s+(\d+\.\d+\.\d+\.\d+))?')

# Headers setup
nso_headers = {
    'Authorization': f'Basic {base64.b64encode(f"{ENV_VARS['NSO_USERNAME']}:{ENV_VARS["NSO_PASSWORD"]}".encode()).decode()}',
    'Content-Type': 'application/yang-data+json',
    'Accept': 'application/yang-data+json'
}
# nautobot_headers = {
#     'Authorization': f'Token {ENV_VARS["NAUTOBOT_TOKEN"]}',
#     'Content-Type': 'application/json',
#     'Accept': 'application/json'
# }

def fetch_nso_devices():
    """Fetches a list of devices from NSO."""

    url = f"{ENV_VARS['NSO_URL']}/restconf/tailf/query"
    payload = {
        "tailf-rest-query:immediate-query": {
            "foreach": "/devices/device",
            "select": [{"label": "name", "expression": "name", "result-type": "string"}]
        }
    }

    response = requests.post(url, headers=nso_headers, json=payload, verify=False)
    devices = response.json().get("tailf-rest-query:query-result", {}).get("result", [])
    return [device["select"][0]["value"] for device in devices]

def get_acl_for_device(device_name):
    """Fetches ACLs for a specified device and processes them."""

    url = f"{ENV_VARS['NSO_URL']}/restconf/data/tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:access-list"
    response = requests.get(url, headers=nso_headers, verify=False)

    if response.status_code == 200:
        acl_data = response.json().get("tailf-ned-cisco-ios:access-list", {}).get("access-list", [])
        for acl in acl_data:
            rules = acl.get('rule', [])
            for rule in rules:
                process_acl_rule(rule.get('rule'))
    else:
        print(f"Failed to fetch ACLs for {device_name}: {response.status_code}")

def process_acl_rule(rule_text):
    """Processes a single ACL rule, extracting IPs and pushing to Nautobot."""

    match = ip_pattern.search(rule_text)
    if match:
        ip_address = match.group(1)
        mask = match.group(2)
        if mask:
            cidr = convert_to_cidr(mask)
            full_ip = f"{ip_address}/{cidr}"
        else:
            full_ip = f"{ip_address}/32"
        push_ip_to_nautobot(full_ip)

def convert_to_cidr(mask):
    """Converts a subnet mask to CIDR notation."""

    return sum([bin(int(x)).count('1') for x in mask.split('.')])

def push_ip_to_nautobot(ip_address):
    """Pushes an IP address to Nautobot."""

    namespace_id = "fa8052af-7f81-4818-8eab-d7f08ed192a3"  # Example ID, replace with actual if different
    status_id = "cd5378a5-ed32-4f75-9e9e-980f4280e7c1"  # Example status ID, replace with actual if different

    try:
        status = Status.objects.get(pk=status_id)
    except Status.DoesNotExist:
        print(f"Status with ID {status_id} does not exist.")
        return

    try:
        nautobot.ipam.ip_addresses.create(
            address=ip_address,
            status=status,
            assigned_object_id=namespace_id,
            assigned_object_type="extras.namespace",
            type="host"
        )
        print(f"IP {ip_address} pushed to Nautobot successfully.")
    except Exception as e:
        print(f"Failed to push IP {ip_address} to Nautobot: {e}")

# def push_ip_to_nautobot(ip_address): # TODO: CHANGE DATA VARIABLE
#     """Pushes an IP address to Nautobot."""

#     url = f"{ENV_VARS['NAUTOBOT_URL']}/ipam/ip-addresses/"
#     data = {
# 			  "address": ip_address,
#         "namespace": {
#             "id": "fa8052af-7f81-4818-8eab-d7f08ed192a3",  # Example ID, replace with actual if different
#             "object_type": "app_label.modelname",  # Adjust as necessary
#             "url": "fa8052af-7f81-4818-8eab-d7f08ed192a3"  # This seems incorrect; adjust based on actual requirements
#         },
#         "type": "host",  # Assuming this is constant for your use case
#         "status": {
#             "id": "cd5378a5-ed32-4f75-9e9e-980f4280e7c1",  # Example status ID, replace with actual if different
#             "object_type": "app_label.modelname",  # Adjust as necessary
#             "url": "https://IP/extras/statuses/cd5378a5-ed32-4f75-9e9e-980f4280e7c1"
#         }
#     }

#     response = requests.post(url, headers=nautobot_headers, json=data, verify=False)

#     if response.status_code in [200, 201]:
#         print(f"IP {ip_address} pushed to Nautobot successfully.")
#     else:
#         print(f"Failed to push IP {ip_address} to Nautobot: {response.text}")

def main():
    devices = fetch_nso_devices()
    for device_name in devices:
        print(f"Processing device: {device_name}")
        get_acl_for_device(device_name)

if __name__ == "__main__":
    main()
