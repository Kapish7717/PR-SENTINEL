FROM python:3.12-slim

# Install system dependencies needed for compiling packages and postgres drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose port (Render sets PORT dynamically, but this is good documentation)
EXPOSE 8000

# Start command: runs the FastAPI webhook app using Uvicorn
# Dynamically binds to the PORT environment variable provided by Render, defaulting to 8000
CMD ["sh", "-c", "uvicorn webhook:app --host 0.0.0.0 --port ${PORT:-8000}"]
