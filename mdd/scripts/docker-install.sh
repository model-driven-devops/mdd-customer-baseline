#!/bin/bash

# Update package listings
sudo apt update

# Install necessary packages for Docker installation
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository to APT sources
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

# Update package listings again after adding new repository
sudo apt update

# Install Docker
sudo apt install -y docker-ce

# Add the current user to the Docker group
sudo usermod -aG docker $USER

echo "Docker installation and user modification completed."