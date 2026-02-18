# Getting Started with WebOS

This tutorial will guide you from a fresh clone to a fully running WebOS development environment.

## Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/sanal/webos.git
   cd webos
   ```

2. **Start Infrastructure**
   ```bash
   docker-compose up -d
   ```

3. **Install Dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

4. **Launch WebOS**
   ```bash
   python run.py
   ```

## Prerequisites

- **Python 3.11+**: The core framework uses advanced type hinting and `contextvars`.
- **Docker & Docker Compose**: Required for MongoDB, Redis (TaskIQ), and MinIO (S3).
- **Git**: For version control.

## Step-by-Step Setup

### 1. Backing Services
WebOS requires several services to operate. We provide a `docker-compose.yml` that handles this:
- **MongoDB**: Primary document storage (Beanie).
- **Redis**: Task broker for background workers.
- **MinIO**: S3-compatible local storage for testing.

```bash
docker-compose up -d
```
Verify they are running with `docker-compose ps`.

### 2. Python Environment
We recommend using a virtual environment.

```bash
python -m venv .venv
# Activate
source .venv/bin/activate # Linux/Mac
.venv\Scripts\activate    # Windows
```

Install the package in editable mode:
```bash
pip install -e .
```

### 3. Environment Variables
Create a `.env` file in the root (a `.env.example` is provided if available, otherwise use defaults):

```env
PROJECT_NAME="WebOS Dev"
SECRET_KEY="your-super-secret-key"
MONGO_URL="mongodb://localhost:27017"
REDIS_URL="redis://localhost:6380"
```

### 4. Running the App
Start the main server:
```bash
python run.py
```
Wait for the log: `NiceGUI ready to go on http://localhost:8000`.

Open your browser to [http://localhost:8000](http://localhost:8000).

---

## Next Steps
- Learn how to [Create Your First Module](../tutorials/create_module.md).
- Explore the [Architecture Overview](../concepts/architecture.md).
- Check out the [Full System Walkthrough](../tutorials/system_walkthrough.md).
