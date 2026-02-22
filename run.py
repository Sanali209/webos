import subprocess
import sys
import os
import time

# Ensure the project root is on the path no matter how this script is invoked
# (VS Code debugger, terminal, etc.)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))


def run_subprocess():
    """Spawn Uvicorn + TaskIQ as child processes (CLI / terminal usage)."""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + env.get("PYTHONPATH", "")

    uvicorn_cmd = [
        sys.executable, "-u", "-m", "uvicorn",
        "src.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
    ]
    worker_cmd = [
        sys.executable, "-u", "-m", "taskiq", "worker",
        "src.core.tasks:broker",
    ]

    processes = []
    try:
        processes.append(subprocess.Popen(uvicorn_cmd, env=env))
        processes.append(subprocess.Popen(worker_cmd, env=env))

        print("\n✅ WebOS started successfully!")
        print("🔗 UI: http://localhost:8000")
        print("🛠️  API: http://localhost:8000/docs")
        print("Press Ctrl+C to stop both processes.\n")

        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"\n⚠️ Process {p.args} exited with code {p.returncode}")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n🛑 Stopping WebOS...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print("👋 Goodbye!")


def run_direct():
    """Run Uvicorn directly in this process (VS Code debugger / IDE usage).
    
    This is the preferred mode when debugging because:
    - The debugger is attached to the correct process
    - The correct .venv interpreter is used automatically
    - Breakpoints inside src/ work properly
    """
    import uvicorn

    # Start TaskIQ worker as a background subprocess still
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + env.get("PYTHONPATH", "")
    worker = subprocess.Popen(
        [sys.executable, "-u", "-m", "taskiq", "worker", "src.core.tasks:broker"],
        env=env,
    )

    try:
        print("🚀 Starting WebOS Server (direct mode)...")
        print("🔗 UI: http://localhost:8000")
        print("🛠️  API: http://localhost:8000/docs\n")
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )
    finally:
        worker.terminate()
        worker.wait()
        print("👋 Goodbye!")


if __name__ == "__main__":
    # Detect if running under a debugger (VS Code sets one of these)
    is_debug = (
        os.environ.get("DEBUGPY_PROCESS_ID")
        or os.environ.get("PYDEVD_USE_CYTHON")
        or (hasattr(sys, "gettrace") and sys.gettrace() is not None)
    )

    if is_debug:
        run_direct()
    else:
        print("🚀 Starting WebOS Server...")
        run_subprocess()

