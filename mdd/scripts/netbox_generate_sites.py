import os
import csv
from urllib.parse import urljoin
from pynetbox import api
import load_env_vars

ENV_VARS = {
    "NETBOX_URL": None,
    "NETBOX_TOKEN": None
}
# Path to your CSV file
csv_file_path = './docs/netbox_sites.csv'

ENV_VARS = load_env_vars.load_env_vars(os.environ, ENV_VARS)

# Initialize NetBox API
netbox = api(url=ENV_VARS['NETBOX_URL'], token=ENV_VARS['NETBOX_TOKEN'])

def create_region(region_name):
    """Create a region in NetBox if it doesn't already exist."""
    if not region_name:
        return None

    try:
        region = netbox.dcim.regions.get(name=region_name)
        print(f"Region '{region_name}' already exists.")
        return region.id
    except netbox.core.query.RequestError:
        try:
            region = netbox.dcim.regions.create(name=region_name, slug=region_name.lower())
            print(f"Region '{region_name}' created successfully.")
            return region.id
        except Exception as e:
            print(f"Failed to create region '{region_name}': {e}")
            return None

def create_site(row):
    """Create a site in NetBox using row data from the CSV"""
    region_id = create_region(row['Region'])

    try:
        site = netbox.dcim.sites.create(
            name=row['Name'],
            slug=row['Slug'],
            status='active' if row['Active'] == 'Active' else 'inactive',
            region=region_id,
            latitude=row['Latitude'] if row['Latitude'] else None,
            longitude=row['Longitude'] if row['Longitude'] else None,
            description=row['Comments']
        )
        print(f"Site '{row['Name']}' created successfully.")
    except Exception as e:
        print(f"Failed to create site '{row['Name']}': {e}")

def main():
    # Read the CSV file and process each row
    with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            create_site(row)

if __name__ == "__main__":
    main()


# headers = {'Authorization': f'Token {ENV_VARS["NETBOX_TOKEN"]}', 'Content-Type': 'application/json'}

# # Path to your CSV file
# csv_file_path = './docs/netbox_sites.csv'

# def create_region(region_name):
#     """Create a region in NetBox if it doesn't already exist."""

#     if region_name == '':
#         return None

#     url = urljoin(ENV_VARS['NETBOX_URL'], 'api/dcim/regions/')
#     response = requests.get(url, headers=headers, params={'name': region_name}, verify=False)  # Added verify=False here

#     if response.status_code != 200:
#         print(f"Failed to check if region '{region_name}' exists.")
#         return None

#     if response.json()['count'] > 0:
#         print(f"Region '{region_name}' already exists.")
#         return response.json()['results'][0]['id']

#     # Region doesn't exist - create it
#     data = {'name': region_name, 'slug': region_name.lower()}
#     create_response = requests.post(url, json=data, headers=headers, verify=False)  # And here

#     if create_response.status_code in [200, 201]:
#         print(f"Region '{region_name}' created successfully.")
#         return create_response.json()['id']

#     print(f"Failed to create region '{region_name}'.")
#     return None

# def create_site(row):
#     """Create a site in NetBox using row data from the CSV"""

#     region_id = create_region(row['Region'])
#     url = urljoin(ENV_VARS['NETBOX_URL'], 'api/dcim/sites/')
#     headers = {'Authorization': f'Token {NETBOX_TOKEN}', 'Content-Type': 'application/json'}
#     data = {
#         'name': row['Name'],
#         'slug': row['Slug'],
#         'status': 'active' if row['Active'] == 'Active' else 'inactive',
#         'region': region_id,
#         'latitude': row['Latitude'] if row['Latitude'] else None,
#         'longitude': row['Longitude'] if row['Longitude'] else None,
#         'description': row['Comments'],
#     }

#     response = requests.post(url, json=data, headers=headers, verify=False)  # Added verify=False here

#     if response.status_code in [200, 201]:
#         print(f"Site '{row['Name']}' created successfully.")
#     else:
#         print(f"Failed to create site '{row['Name']}': {response.text}")

# # Read the CSV file and process each row
# with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
#     reader = csv.DictReader(csvfile)
#     for row in reader:
#         create_site(row)
