
FROM madnight/docker-alpine-wkhtmltopdf:0.12.6-alpine

# Install Python and pip
RUN apk add --no-cache python3 py3-pip && pip3 install --upgrade pip

# Set workdir
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Expose port
EXPOSE 10000

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
