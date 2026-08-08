import subprocess
import sys
import time

if __name__ == "__main__":
    # 1. Start Uvicorn backend in the background
    print("Starting FastAPI backend on http://127.0.0.1:8000 ...")
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "backend.main:app",  # <-- Update 'backend.main:app' to match your backend path
        "--host", "127.0.0.1", 
        "--port", "8000", 
        "--reload"
    ])

    # Give the backend 2 seconds to launch before starting Streamlit
    time.sleep(2)

    # 2. Run Streamlit frontend in the foreground
    print("Starting Streamlit frontend...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/app.py"])
    except KeyboardInterrupt:
        pass
    finally:
        # Automatically stop the backend process when Streamlit exits (Ctrl+C)
        print("\nStopping backend server...")
        backend_process.terminate()