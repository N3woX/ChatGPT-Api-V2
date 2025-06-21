FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED 1 \
    PIP_NO_CACHE_DIR 1 \
    PIP_DISABLE_PIP_VERSION_CHECK 1

# Install essential packages for adding Google Chrome's repository and downloading Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Add Google Chrome's official signing key and repository
# This ensures that apt can verify and download Google Chrome Stable.
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome Stable and all its recommended dependencies,
# plus other common dependencies for headless Selenium environments.
# Combine these installations for efficiency and a smaller image.
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
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
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-noto-color-emoji \
    xvfb \
    libu2f-udev \
    libvulkan1 \
    libpangocairo-1.0-0 \
    libegl1 \
    libgbm1 \
    libglvnd0 \
    libxshmfence6 \
    fonts-noto \
    fonts-symbola \
    # Clean up apt caches to minimize image size
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
