FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED 1 \
    PIP_NO_CACHE_DIR 1 \
    PIP_DISABLE_PIP_VERSION_CHECK 1

# Install essential packages for adding Google Chrome's repository and downloading Chrome
# and the core dependencies that Google Chrome Stable doesn't implicitly pull
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    xvfb \
    # Core system libs often needed for headless Chrome, even with google-chrome-stable
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
    libgbm-dev \
    libappindicator3-1 \
    libxcb1 \
    libxkbcommon0 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libpangocairo-1.0-0 \
    libegl1 \
    libgbm1 \
    libglvnd0 \
    libxshmfence6 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Add Google Chrome's official signing key and repository using a more modern method
# This ensures that apt can verify and download Google Chrome Stable reliably.
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome Stable and fonts (fonts might not be pulled by google-chrome-stable directly)
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
