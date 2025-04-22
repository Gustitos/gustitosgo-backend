FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system libraries required for wkhtmltopdf and Python
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    build-essential \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    python3 \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf manually (precompiled version avoids dependency issues)
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6/wkhtmltox_0.12.6-1.buster_amd64.deb && \
    apt install -y ./wkhtmltox_0.12.6-1.buster_amd64.deb && \
    rm wkhtmltox_0.12.6-1.buster_amd64.deb

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
