FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    python3-pip \
    libffi-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libxml2-dev \
    libxslt1-dev \
    # fontconfig is important for WeasyPrint to find fonts
    fontconfig \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure the templates directory will be copied (even if it doesn't exist yet locally, this line prepares for it)
# If your templates are inside the 'user-service' directory being copied by 'COPY . .', this explicit copy might be redundant
# but it's good to be explicit if templates are at the root of the 'user-service' context.
# Assuming 'templates' will be at /app/templates, and 'main.py' is at /app/main.py
# The 'COPY . .' above should handle this if 'templates' is part of the build context.

WORKDIR /app
# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
