#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status. This helps in debugging.
set -e

echo "--- Updating apt package list ---"
# Update the package list to ensure we can find the latest versions of packages
apt-get update -y # Removed 'sudo'

echo "--- Installing Chrome/Chromium system dependencies ---"
# Install all necessary system libraries for headless Chrome to run
# This is a comprehensive list to cover most scenarios.
apt-get install -y \ # Removed 'sudo'
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libappindicator1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libgbm-dev \
    libindicator7 \
    libappindicator3-1 \
    libprotobuf8 \
    libqtmultimediakit1 \
    libxcb1 \
    libxkbcommon0 \
    xdg-utils \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-noto-color-emoji \
    --no-install-recommends

echo "--- Cleaning up apt cache ---"
# Clean up the apt cache to save disk space on the Render instance
rm -rf /var/lib/apt/lists/* # Removed 'sudo'

echo "--- Installing Python dependencies ---"
# Install your Python packages listed in requirements.txt
pip install -r requirements.txt

echo "--- Build script finished successfully ---"