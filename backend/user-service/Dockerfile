FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
COPY migrate.sh /app
RUN chmod +x migrate.sh
WORKDIR /app
# Run the FastAPI application
CMD ["./migrate.sh","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
