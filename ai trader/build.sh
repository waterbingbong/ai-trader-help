#!/bin/bash

# build.sh - Installation script for AI Trading Assistant dependencies
# This script installs the ta-lib C library and Python dependencies

echo "Starting build process for AI Trading Assistant..."

# Update package lists
echo "Updating package lists..."
apt-get update

# Install build essentials
echo "Installing build dependencies..."
apt-get install -y build-essential wget

# Download and install TA-Lib
echo "Downloading TA-Lib..."
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
echo "Extracting TA-Lib..."
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
echo "Configuring TA-Lib..."
./configure --prefix=/usr
echo "Building TA-Lib..."
make
echo "Installing TA-Lib..."
make install
cd ..

# Clean up
echo "Cleaning up..."
rm -rf ta-lib-0.4.0-src.tar.gz ta-lib/

# Set environment variables for TA-Lib
echo "Setting environment variables for TA-Lib..."
export TA_LIBRARY_PATH=/usr/lib
export TA_INCLUDE_PATH=/usr/include

# Install NumPy first (required for ta-lib)
echo "Installing NumPy..."
pip install numpy

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install TA-Lib Python wrapper
echo "Installing TA-Lib Python wrapper..."
# Try direct installation first
pip install --global-option=build_ext --global-option="-L/usr/lib/" --global-option="-I/usr/include/" ta-lib

# If direct installation fails, try from GitHub
if [ $? -ne 0 ]; then
    echo "Direct installation failed, trying from GitHub..."
    pip install git+https://github.com/mrjbq7/ta-lib.git@master
fi

echo "Build process completed successfully!"