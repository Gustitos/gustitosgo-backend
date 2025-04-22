# ✅ Use image that already includes wkhtmltopdf
FROM ghcr.io/puppeteer/wkhtmltopdf:latest

# Set working directory
WORKDIR /app

# Install Python manually
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copy code and install Python dependencies
COPY . /app
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the FastAPI app port
EXPOSE 10000

# Start the app using uvicorn (assuming main.py is in root)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
