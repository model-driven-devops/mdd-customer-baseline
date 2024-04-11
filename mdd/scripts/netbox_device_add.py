import requests
import urllib3
import json
import os
import load_env_vars

ENV_VARS = {
    "ENV_VARS['NETBOX_URL']": None,
    "NETBOX_TOKEN": None,
    "NSO_URL": None,
    "NSO_USERNAME": None,
    "NSO_PASSWORD": None,
    "DEVICE_NAME": None,
    "PLATFORM_URL": None
}

ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)

HEADERS = {"Authorization": f"Token {ENV_VARS['NETBOX_TOKEN']}", "Content-Type": "application/json", "Accept": "application/json"}

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_or_create_device_type(platform_data, headers, ENV_VARS['NETBOX_URL']):
    """
    Ensures the device type exists in NetBox based on the NSO platform data,
    and returns the device type ID.
    """

    model = platform_data["tailf-ncs:platform"]["model"]
    slug = model.replace("-", "_").lower()

    # Check if the device type already exists
    search_response = requests.get(f"{ENV_VARS['NETBOX_URL']}/api/dcim/device-types/?slug={slug}", headers=headers, verify=False)

    if search_response.status_code != 200:
        return None


    if search_response.json()['count'] > 0:
        # Device type exists
        return search_response.json()["results"][0]["id"]

    # Device type does not exist, proceed with creation
    payload = {
        "manufacturer": "2",  # Replace with actual manufacturer ID
        "model": model,
        "slug": slug,
        "part_number": model,  # Using model as part_number for simplicity
        "name": model
    }

    response = requests.post(f"{ENV_VARS['NETBOX_URL']}/api/dcim/device-types/", headers=headers, data=json.dumps(payload), verify=False)

    if response.status_code not in [200, 201]:
        print(f"Failed to add device type {model}: {response.status_code}, {response.text}")
        return None

    print(f"Successfully added device type: {model}")
    return response.json()["id"]

def update_device(platform_data, device_type_id, headers, ENV_VARS['NETBOX_URL']):
    """
    Updates an existing device in NetBox with the device type based on NSO platform data.
    """

    device_name = ""
    serial_number = platform_data["tailf-ncs:platform"]["serial-number"]

    # Attempt to find the device in NetBox
    search_response = requests.get(f"{ENV_VARS['NETBOX_URL']}/api/dcim/devices/?name={device_name}", headers=headers, verify=False)

    if search_response.status_code != 200:
        return

    if search_response.json()['count'] == 0:
        print(f"Device {device_name} does not exist. Skipping.")
        return

    device_id = search_response.json()["results"][0]["id"]
    payload = {
        "device_type": device_type_id,
        "serial": serial_number
    }

    update_response = requests.patch(f"{ENV_VARS['NETBOX_URL']}/api/dcim/devices/{device_id}/", headers=headers, data=json.dumps(payload), verify=False)

    if update_response.status_code in [200, 201, 204]:
        print(f"Successfully updated device: {device_name}")
    else:
        print(f"Failed to update device {device_name}: {update_response.status_code}, {update_response.text}")

# Make the GET request to retrieve the platform information
response = requests.get(ENV_VARS['PLATFORM_URL'], auth=(ENV_VARS['NSO_USERNAME'], ENV_VARS['NSO_PASSWORD']), headers={"Accept": "application/yang-data+json"}, verify=False)
if response.status_code != 200:
    print(f"Failed to retrieve platform information: {response.status_code}, {response.text}")
    os._exit(1)

print("Platform information retrieved successfully")
platform_data = response.json()
device_type_id = get_or_create_device_type(platform_data, HEADERS, ENV_VARS['NETBOX_URL'])
if device_type_id:
    update_device(platform_data, device_type_id, HEADERS, ENV_VARS['NETBOX_URL'])
