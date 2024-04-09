import requests
import urllib3
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_or_create_device_type(platform_data, headers, netbox_url):
    """
    Ensures the device type exists in NetBox based on the NSO platform data,
    and returns the device type ID.
    """
    model = platform_data["tailf-ncs:platform"]["model"]
    slug = model.replace("-", "_").lower()
    
    # Check if the device type already exists
    search_response = requests.get(f"{netbox_url}/api/dcim/device-types/?slug={slug}", headers=headers, verify=False)
    if search_response.status_code == 200 and search_response.json()['count'] == 0:
        # Device type does not exist, proceed with creation
        payload = {
            "manufacturer": "2",  # Replace with actual manufacturer ID
            "model": model,
            "slug": slug,
            "part_number": model,  # Using model as part_number for simplicity
            "name": model
        }
        response = requests.post(f"{netbox_url}/api/dcim/device-types/", headers=headers, data=json.dumps(payload), verify=False)
        if response.status_code in [200, 201]:
            print(f"Successfully added device type: {model}")
            return response.json()["id"]
        else:
            print(f"Failed to add device type {model}: {response.status_code}, {response.text}")
            return None
    else:
        # Device type exists
        return search_response.json()["results"][0]["id"]

def update_device(platform_data, device_type_id, headers, netbox_url):
    """
    Updates an existing device in NetBox with the device type based on NSO platform data.
    """
    device_name = ""
    serial_number = platform_data["tailf-ncs:platform"]["serial-number"]
    # Attempt to find the device in NetBox
    search_response = requests.get(f"{netbox_url}/api/dcim/devices/?name={device_name}", headers=headers, verify=False)
    if search_response.status_code == 200 and search_response.json()['count'] > 0:
        device_id = search_response.json()["results"][0]["id"]
        payload = {
						"device_type": device_type_id,
				  	"serial": serial_number 
				}
        update_response = requests.patch(f"{netbox_url}/api/dcim/devices/{device_id}/", headers=headers, data=json.dumps(payload), verify=False)
        if update_response.status_code in [200, 201, 204]:
            print(f"Successfully updated device: {device_name}")
        else:
            print(f"Failed to update device {device_name}: {update_response.status_code}, {update_response.text}")
    else:
        print(f"Device {device_name} does not exist. Skipping.")

# Setup for NetBox and NSO
netbox_url = 
netbox_token =
headers = {"Authorization": f"Token {netbox_token}", "Content-Type": "application/json", "Accept": "application/json"}
nso_url =
nso_username = 
nso_password =
device_name = 
platform_url = 

# Make the GET request to retrieve the platform information
response = requests.get(platform_url, auth=(nso_username, nso_password), headers={"Accept": "application/yang-data+json"}, verify=False)
if response.status_code == 200:
    print("Platform information retrieved successfully")
    platform_data = response.json()
    device_type_id = get_or_create_device_type(platform_data, headers, netbox_url)
    if device_type_id:
        update_device(platform_data, device_type_id, headers, netbox_url)
else:
    print(f"Failed to retrieve platform information: {response.status_code}, {response.text}")
