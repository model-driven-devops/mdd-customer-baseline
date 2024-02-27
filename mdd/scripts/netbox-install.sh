!/bin/bash

# Define the NetBox directory
HOME_DIR=/home/ubuntu/


# Initialize an empty repository and fetch the contents into the existing directory
echo "Cloning the NetBox Docker repository into $HOME_DIR."
cd "$HOME_DIR"
sudo git clone https://github.com/netbox-community/netbox-docker.git

# Change directory back to NETBOX_DIR
cd netbox-docker

# Create or overwrite the docker-compose.override.yml with custom content
echo "Creating docker-compose.override.yml."
sudo tee docker-compose.override.yml <<EOF
version: '3.4'
services:
  netbox:
    ports:
      - 8000:8080
    healthcheck:
      start_period: 90s
EOF


# Copy the netbox.service systemd service file to the systemd directory
echo "Configuring netbox.service systemd service."
sudo cp /tmp/netbox.service /etc/systemd/system/netbox.service

# Reload systemd to recognize the new service file
sudo systemctl daemon-reload

# Enable the NetBox service to start at boot
sudo systemctl enable netbox.service

# Optionally, start the service immediately
sudo systemctl start netbox.service

echo "NetBox setup completed and service configured."