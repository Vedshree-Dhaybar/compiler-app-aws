#!/bin/bash
echo "Installing application dependencies..."

# Update package lists
apt-get update -y

# Install python3-pip and python3-venv if they aren't already there
apt-get install -y python3-pip python3-venv

# Create an application directory if it doesn't exist yet
mkdir -p /home/ubuntu/compiler-app
