FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    gcc \
    g++ \
    git \
    python3-dev \
    build-essential \
    procps \
    libgl1 \
    libglib2.0-0 \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files
COPY web /app/web

# Create virtual environment and install dependencies
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r search/requirements.txt \
    && /opt/venv/bin/python -m nltk.downloader \
        punkt averaged_perceptron_tagger stopwords

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Expose backend port
EXPOSE 8080

# Start the backend server
CMD ["bash", "/app/web/start_server.sh", "0.0.0.0", "8080"]

