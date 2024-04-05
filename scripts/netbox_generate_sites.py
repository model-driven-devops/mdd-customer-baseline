import csv
import requests
import os
import urllib3
from urllib.parse import urljoin
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
netbox_token = os.getenv('NETBOX_TOKEN')
netbox_url = os.getenv('NETBOX_URL')

def create_region(region_name):
    """Create a region in NetBox if it doesn't already exist."""
    if region_name == '':
        return None
    url = urljoin(netbox_url, 'api/dcim/regions/')
    headers = {'Authorization': f'Token {netbox_token}', 'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers, params={'name': region_name}, verify=False)  # Added verify=False here
    if response.status_code == 200 and response.json()['count'] == 0:
        data = {'name': region_name, 'slug': region_name.lower()}
        create_response = requests.post(url, json=data, headers=headers, verify=False)  # And here
        if create_response.status_code in [200, 201]:
            print(f"Region '{region_name}' created successfully.")
            return create_response.json()['id']
        else:
            print(f"Failed to create region '{region_name}'.")
            return None
    elif response.json()['count'] > 0:
        print(f"Region '{region_name}' already exists.")
        return response.json()['results'][0]['id']
    else:
        print(f"Failed to check if region '{region_name}' exists.")
        return None

def create_site(row):
    """Create a site in NetBox using row data from the CSV."""
    region_id = create_region(row['Region'])
    url = urljoin(netbox_url, 'api/dcim/sites/')
    headers = {'Authorization': f'Token {netbox_token}', 'Content-Type': 'application/json'}
    data = {
        'name': row['Name'],
        'slug': row['Slug'],
        'status': 'active' if row['Active'] == 'Active' else 'inactive',
        'region': region_id,
        'latitude': row['Latitude'] if row['Latitude'] else None,
        'longitude': row['Longitude'] if row['Longitude'] else None,
        'description': row['Comments'],
    }
    response = requests.post(url, json=data, headers=headers, verify=False)  # Added verify=False here
    if response.status_code in [200, 201]:
        print(f"Site '{row['Name']}' created successfully.")
    else:
        print(f"Failed to create site '{row['Name']}': {response.text}")

# Path to your CSV file
csv_file_path = './docs/netbox_sites.csv'

# Read the CSV file and process each row
with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        create_site(row)
