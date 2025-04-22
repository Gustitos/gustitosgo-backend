FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libxrender1 \
    libxext6 \
    libfontconfig1 && \
    rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf manually from stable precompiled .deb
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb && \
    apt install -y ./wkhtmltox_0.12.6-1.buster_amd64.deb && \
    rm wkhtmltox_0.12.6-1.buster_amd64.deb

# Copy code and install Python packages
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose the FastAPI app port
EXPOSE 10000

# Start the FastAPI app from main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
