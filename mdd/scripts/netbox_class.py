import json
import requests

class netbox_helper():
  def __init__(self,NETBOX_URL, NETBOX_HEADERS): 
      self.netbox_url=NETBOX_URL
      self.netbox_headers=NETBOX_HEADERS

  def fetch_netbox_devices(self):
      """Fetch all devices from NetBox."""
      url = f"{self.netbox_url}/api/dcim/devices/"
      response = requests.get(url, headers=self.netbox_headers, verify=False)
      if response.status_code == 200:
          return response.json().get('results', [])
      else:
          print(f"Failed to retrieve devices from NetBox: {response.status_code}, {response.text}")
          return []
