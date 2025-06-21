FROM python:3.10-slim-buster

ENV PYTHONUNBUFFERED 1 \
    PIP_NO_CACHE_DIR 1 \
    PIP_DISABLE_PIP_VERSION_CHECK 1 \
    DEBIAN_FRONTEND noninteractive

# Install only the absolute essentials required to add the Chrome repository and XVFB
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    unzip \
    xvfb \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Add Google Chrome's official signing key and repository
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome Stable and necessary fonts.
# google-chrome-stable is designed to pull its own extensive dependencies.
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-noto-color-emoji \
    fonts-noto \
    fonts-symbola \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
