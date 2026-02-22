"""
run_e2e.py — Convenience script to start the WebOS server and run Playwright E2E tests.

Usage:
    python run_e2e.py
    python run_e2e.py --headed        # Show browser window
    python run_e2e.py -k TestLaunchpad  # Run only a specific test class
"""
import os
import sys
import time
import socket
import subprocess
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))


def is_port_open(port: int) -> bool:
    for host in ("127.0.0.1", "::1"):
        try:
            family = socket.AF_INET6 if ":" in host else socket.AF_INET
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((host, port))
                return True
        except OSError:
            pass
    return False


def wait_for_server(port: int, timeout: int = 60) -> bool:
    print(f"⏳ Waiting up to {timeout}s for server on port {port}...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_open(port):
            print("✅ Server is ready!\n")
            return True
        time.sleep(1)
    return False


def main():
    parser = argparse.ArgumentParser(description="Run WebOS E2E tests")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("-k", type=str, default=None, help="Pytest -k filter expression")
    args = parser.parse_args()

    server_process = None

    # Start server if not already running
    if is_port_open(args.port):
        print(f"✅ Server already running on port {args.port} — using it.\n")
    else:
        print("🚀 Starting WebOS server...")
        env = os.environ.copy()
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        server_process = subprocess.Popen(
            [sys.executable, "-u", "-m", "uvicorn", "src.main:app",
             "--host", "127.0.0.1", f"--port={args.port}"],
            cwd=ROOT,
            env=env,
        )
        if not wait_for_server(args.port, timeout=90):
            print("❌ Server failed to start within 90 seconds.")
            if server_process:
                server_process.terminate()
            sys.exit(1)

    # Build pytest command
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        "tests/e2e/test_dam_ui.py",
        "-v",
        "--timeout=45",
        "--browser", "chromium",
        f"--base-url=http://127.0.0.1:{args.port}",
    ]
    if args.headed:
        pytest_cmd.append("--headed")
    if args.k:
        pytest_cmd.extend(["-k", args.k])

    print("🧪 Running Playwright E2E tests...\n")
    result = subprocess.run(pytest_cmd, cwd=ROOT)

    # Cleanup
    if server_process:
        print("\n🛑 Stopping test server...")
        server_process.terminate()
        server_process.wait(timeout=5)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
