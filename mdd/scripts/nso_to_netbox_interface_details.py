import requests
import json
import base64
import os

# Suppress only the single InsecureRequestWarning from urllib3 needed
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Environment Variables
NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
NSO_URL = os.getenv('NSO_URL')
NSO_USERNAME = os.getenv('NSO_USERNAME')
NSO_PASSWORD = os.getenv('NSO_PASSWORD')

# Headers
netbox_headers = {"Authorization": f"Token {NETBOX_TOKEN}", "Content-Type": "application/json"}
nso_auth = base64.b64encode(f"{NSO_USERNAME}:{NSO_PASSWORD}".encode()).decode('utf-8')
nso_headers = {"Authorization": f"Basic {nso_auth}", "Accept": "application/yang-data+json", "Content-Type": "application/yang-data+json"}

def get_netbox_devices():
    url = f"{NETBOX_URL}/api/dcim/devices/"
    response = requests.get(url, headers=netbox_headers, verify=False)
    return response.json()['results']

def get_nso_interfaces(device_name):
    url = f"{NSO_URL}/restconf/data/tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/"
    response = requests.get(url, headers=nso_headers, verify=False)
    return response.json().get("tailf-ned-cisco-ios:interface", {})

def get_netbox_vlans():
    url = f"{NETBOX_URL}/api/ipam/vlans/"
    response = requests.get(url, headers=netbox_headers, verify=False)
    vlans = {}
    for vlan in response.json()['results']:
        vlans[vlan['vid']] = vlan['id']
    return vlans

def get_netbox_interface_id(device_id, interface_name):
    """
    Fetches the Netbox interface ID for a given device and interface name.
    """
    url = f"{NETBOX_URL}/api/dcim/interfaces/?device_id={device_id}&name={interface_name}"
    response = requests.get(url, headers=netbox_headers, verify=False)
    if response.status_code == 200 and response.json()['count'] > 0:
        return response.json()['results'][0]['id']
    else:
        print(f"Failed to fetch interface ID for {interface_name} on device ID {device_id}.")
        return None

def update_netbox_interfaces(device_id, device_name, interfaces, netbox_vlans):
    for interface_type, interface_list in interfaces.items():
        for interface in interface_list:
            updated_interface_name = f"{interface_type}{interface['name']}"
            interface_id = get_netbox_interface_id(device_id, interface["name"])
            if not interface_id:
                continue  # Skip this interface if its ID couldn't be retrieved

            tagged_vlans_ids = [netbox_vlans[vid] for vid in interface.get('switchport', {}).get('trunk', {}).get('allowed', {}).get('vlan', {}).get('vlans', []) if vid in netbox_vlans]
            payload = {
                "id": interface_id,
                "device": device_id,
                "name": updated_interface_name,
                "type": "10gbase-t" if "TenGigabitEthernet" in interface_type else "1000base-t",
                "mgmt_only": False,
                "description": interface.get("description", ""),
                "mode": "tagged",
                "tagged_vlans": tagged_vlans_ids
            }
            if 'native' in interface.get('switchport', {}).get('trunk', {}):
                native_vlan = interface['switchport']['trunk']['native']['vlan']
                if native_vlan in netbox_vlans:
                    payload['untagged_vlan'] = netbox_vlans[native_vlan]

            # Using PATCH request to update the interface with the VLAN data
            url = f"{NETBOX_URL}/api/dcim/interfaces/{interface_id}/"
            response = requests.patch(url, headers=netbox_headers, data=json.dumps(payload), verify=False)
            if response.status_code in [200, 201, 204]:
                print(f"Interface {interface['name']} updated successfully for device {device_name}.")
            else:
                print(f"Failed to update interface {interface['name']} for device {device_name}: {response.text}")
def main():
    netbox_devices = get_netbox_devices()
    netbox_vlans = get_netbox_vlans()
    for device in netbox_devices:
        device_name = device['name']
        device_id = device['id']
        nso_interfaces = get_nso_interfaces(device_name)
        update_netbox_interfaces(device_id, device_name, nso_interfaces, netbox_vlans)

if __name__ == "__main__":
    main()
