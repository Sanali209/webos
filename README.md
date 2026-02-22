# WebOS Framework

A Modular Monolith framework designed for rapid development of complex internal tools.

## Features
*   **Modular Architecture**: Pluggy-based plugin system.
*   **Modern Stack**: FastAPI, NiceGUI, Beanie (MongoDB), TaskIQ.
*   **Developer Experience**: Auto-discovery, Type-safety, Hot Reload.

## Getting Started

### Prerequisites

- Python 3.11+
- MongoDB instance (remote or local via Docker)
- Redis instance (for TaskIQ background workers)
- Qdrant instance (for vector search capabilities)
- `ffprobe` executable in your system PATH (required for DAM Video processing)

### Fast Start
1.  Clone the repository:
    ```bash
    git clone https://github.com/your-org/webos.git
    cd webos
    ```
2.  Start backing services:
    ```bash
    docker-compose up -d
    ```
3.  Install dependencies:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    pip install -e .[dev]
    # Linux/Mac
    source .venv/bin/activate
    pip install -e .[dev]
    ```
4.  Run the server:
    ```bash
    uvicorn src.main:app --reload
    ```

## Documentation
See `Docs/` directory for detailed design and architecture documents.
