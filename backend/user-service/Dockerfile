FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN chmod +x migrate.sh
# Run the FastAPI application
CMD ["./migrate.sh", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
