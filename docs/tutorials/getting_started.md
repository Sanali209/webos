# Getting Started Tutorial

This tutorial will walk you through starting the WebOS server from scratch, allowing you to access both the NiceGUI user interface and the FastAPI Swagger docs.

## Prerequisites

1.  Clone the repository and `cd` into it.
2.  Start the background services:
    ```bash
    docker-compose up -d
    ```
3.  Activate your Python 3.11+ virtual environment and install dependencies:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    pip install -e .[dev]
    ```

## Starting the Application

While you can start `uvicorn` and `taskiq` separately, the easiest way to launch the entire WebOS framework is simply by running the `run.py` script.

This script detects your environment and automatically launches both the fast API server and the background workers.

```bash
# Example: Starting the server
python run.py
```

### Expected Output

You should see log output detailing the auto-discovery of modules and then the server starting:

```
🚀 Starting WebOS Server...
INFO:     Started server process [1234]
INFO:     Waiting for application startup.
✅ WebOS started successfully!
🔗 UI: http://localhost:8000
🛠️  API: http://localhost:8000/docs
```

## Exploring WebOS

Once running, try the following:

1.  Open [http://localhost:8000](http://localhost:8000) in your browser. You will see the main WebOS interface rendered by NiceGUI.
2.  Open [http://localhost:8000/docs](http://localhost:8000/docs) to see the automatically generated Swagger API documentation for all discovered modules.

## Next Steps

Now that you have the environment running, let's learn how to [Create Your First Module](./create_module.md).
