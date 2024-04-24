import json
import requests
import load_env_vars
import os


class netbox_helper():
    def __init__(self, headers={}, verify_ssl=False):
        ENV_VARS = {
            "NETBOX_URL" : None,
            "NETBOX_TOKEN" : None
        }
        self.ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)

        self.headers = {'Authorization': f'Token {self.ENV_VARS['NETBOX_TOKEN']}', "Content-Type": "application/json", "Accept": "application/json"}
        self.headers.update(headers)

        self.verify_ssl = verify_ssl

    def get_netbox_devices(self, query=""):
        """Fetch devices from NetBox"""

        url = f"{self.ENV_VARS["NETBOX_URL"]}/api/dcim/devices/{query}"
        response = requests.get(url, headers=self.headers, verify=self.verify_ssl)

        if response.status_code != 200:
            print(f"Failed to retrieve devices from NetBox: {response.status_code}, {response.text}")
            return []

        return response.json().get('results', [])

    def get_netbox_sites(self, query=""):
        """Fetch sites from NetBox"""

        url = f"{self.ENV_VARS["NETBOX_URL"]}/api/dcim/sites/{query}"
        response = requests.get(url, headers=self.headers, verify=self.verify_ssl)

        if response.status_code != 200:
            print(f"Failed to retrieve sites from NetBox: {response.status_code}, {response.text}")
            return []

        return response.json().get('results', [])

    def get_netbox_device_type(self, query=""):
        """Gets device_types"""

        url = f"{self.ENV_VARS['NETBOX_URL']}/api/dcim/device-types/{query}"
        response = requests.get(url, headers=self.headers, verify=self.verify_ssl)

        if response.status_code != 200:
            print(f"Failed to retrieve sites from NetBox: {response.status_code}, {response.text}")
            return []

        return response.json().get('results', [])

    def get_netbox_device_type(self, query=""):
        """Gets device_types"""

        url = f"{self.ENV_VARS['NETBOX_URL']}/api/dcim/device-types/{query}"
        response = requests.get(url, headers=self.headers, verify=self.verify_ssl)

        if response.status_code != 200:
            print(f"Failed to retrieve sites from NetBox: {response.status_code}, {response.text}")
            return []

        return response.json().get('results', [])

    response = requests.post(f"{ENV_VARS['NETBOX_URL']}/api/dcim/device-types/", headers=headers, data=json.dumps(payload), verify=False)
