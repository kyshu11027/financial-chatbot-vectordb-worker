# financial-chatbot-vectordb-worker

Python worker for asynchronously processing user transactions

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Server

To start the server, run:

```bash
LOG_LEVEL=DEBUG gunicorn main:app --workers 6 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8090 --log-level error
```

The server will start at `http://localhost:8090`

## API Documentation

Once the server is running, you can access:

- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`
