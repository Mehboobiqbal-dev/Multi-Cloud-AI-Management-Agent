FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libgomp1 build-essential

# Copy backend source
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Make start.sh executable
RUN chmod +x start.sh

# Run FastAPI
CMD ["./start.sh"]
