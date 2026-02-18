import subprocess
import sys
import os
import signal
import time

def run_server():
    print("🚀 Starting WebOS Server...")
    # Add project root to PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    
    # Start Uvicorn
    # Using sys.executable to ensure we use the same Python interpreter (the .venv)
    uvicorn_cmd = [
        sys.executable, "-u", "-m", "uvicorn", 
        "src.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ]
    
    # Start TaskIQ Worker
    worker_cmd = [
        sys.executable, "-u", "-m", "taskiq", "worker", 
        "src.core.tasks:broker"
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
            # Check if any process has died
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

if __name__ == "__main__":
    run_server()
