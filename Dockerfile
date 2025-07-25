# Stage 1: Install Python backend dependencies
FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential

COPY multi-cloud-agent/backend ./
RUN pip install --no-cache-dir -r requirements.txt

# Set any startup script or environment vars here
RUN chmod +x start.sh

CMD ["./start.sh"]
