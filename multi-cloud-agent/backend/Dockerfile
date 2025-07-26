FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libgomp1

# Copy backend source
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt[aws,azure,gcp]

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
