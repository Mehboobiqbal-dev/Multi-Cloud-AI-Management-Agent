# ----------- Stage 1: Build frontend -----------
FROM node:18 as frontend

WORKDIR /app
COPY multi-cloud-agent/frontend ./frontend
RUN cd frontend && npm install && npm run build


# ----------- Stage 2: Install Python backend dependencies -----------
FROM python:3.11-slim as backend

WORKDIR /app
COPY multi-cloud-agent/backend ./backend
RUN pip install --no-cache-dir -r backend/requirements.txt


# ----------- Final Stage -----------
FROM node:18-slim

WORKDIR /app
COPY --from=frontend /app/frontend/build ./frontend/build
COPY --from=backend /app/backend ./backend

# Set any startup script or environment vars here
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
RUN chmod +x start.sh

CMD ["./start.sh"]
