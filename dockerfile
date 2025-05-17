FROM python:3.9-slim-buster

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app /app

# Set uvloop as default event loop policy (can also be done in code)
ENV PYTHONUNBUFFERED=1

# Run the main app asynchronously
CMD ["python", "main.py"]
