# Multi-Cloud Agent

A unified agent to manage AWS, Azure, and Google Cloud resources from a single prompt, with a visual UI and real-time workflow visualization.

## Features
- **Multi-cloud:** Supports AWS, Azure, and GCP operations from a single prompt.
- **NLP-powered:** Parses natural language prompts to extract intent and execute cloud operations.
- **Visual UI:** See step-by-step workflow, logs, and results for each cloud.
- **Knowledge base:** Built-in docs and error explanations for all operations.
- **Extensible:** Add more operations/providers easily.

## Quick Start

### 1. Clone and Install
```bash
git clone <repo-url>
cd multi-cloud-agent/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../frontend
npm install
```

### 2. Set Up Cloud Credentials
- **AWS:** Set up `~/.aws/credentials` or environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).
- **Azure:** Set `AZURE_SUBSCRIPTION_ID` in your environment. Use `az login` for authentication, or set up a service principal.
- **GCP:** Set `GOOGLE_CLOUD_PROJECT` in your environment. Authenticate with `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS`.

See `.env.example` for environment variable examples.

### 3. Run Backend
```bash
cd ../backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Frontend
```bash
cd ../frontend
npm start
```

- Access the UI at [http://localhost:3000](http://localhost:3000)

## Usage
- Enter prompts like:
  - `List all EC2 instances on AWS`
  - `List all VMs in AWS and Azure`
  - `List all storage buckets in GCP`
- See real-time workflow, results, and error explanations.

## Deployment (Docker)

### Backend Dockerfile
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/ .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY frontend/ .
RUN npm install && npm run build
EXPOSE 3000
CMD ["npx", "serve", "-s", "build"]
```

## Testing
```bash
cd backend
source venv/bin/activate
python -m unittest test_intent_extractor.py
python -m unittest test_cloud_handlers.py
python -m unittest test_api.py
```

## Extending
- Add more operations in `cloud_handlers.py` and `knowledge_base.py`.
- Expand the UI in `frontend/src/App.js`.

## License
MIT