FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system libraries and wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    xz-utils \
    build-essential \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    wkhtmltopdf \
    python3 \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
