# Use a Python base image that's compatible with Debian/Ubuntu's apt packages.
# python:3.10-slim-bullseye is a good choice for a lean image.
FROM python:3.10-slim-bullseye

# Set environment variables for Python.
ENV PYTHONUNBUFFERED 1 \
    PIP_NO_CACHE_DIR 1 \
    PIP_DISABLE_PIP_VERSION_CHECK 1

# Install system dependencies for Chrome/Chromium.
# This list is comprehensive and covers most common requirements.
# We run apt-get update first, then install, then clean up the apt lists.
RUN apt-get update && apt-get install -y \
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
    libappindicator3-1 \
    libxcb1 \
    libxkbcommon0 \
    xdg-utils \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-noto-color-emoji \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Create a working directory inside the Docker image
WORKDIR /app

# Copy your requirements.txt file into the image
COPY requirements.txt .

# Install your Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of your application code into the image
COPY . .

# Expose the port your Flask app will run on. Render uses this.
EXPOSE 5000

# Define the command to run your Flask application when the container starts.
# We'll use Gunicorn for production.
# Replace 'main:app' if your Flask app instance is named differently or in another file.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]