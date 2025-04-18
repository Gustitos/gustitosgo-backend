
FROM python:3.10-slim

# Install system dependencies and wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    build-essential \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    xz-utils && \
    wget http://ftp.us.debian.org/debian/pool/main/o/openssl1.1/libssl1.1_1.1.1n-0+deb10u3_amd64.deb && \
    dpkg -i libssl1.1_1.1.1n-0+deb10u3_amd64.deb && \
    wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb && \
    dpkg -i wkhtmltox_0.12.6-1.buster_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
