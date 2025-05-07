# import os
# import subprocess
# import threading
# import time

# def start_fastapi():
#     print("Starting FastAPI server...")
#     os.environ["PYTHONUNBUFFERED"] = "1"
#     subprocess.run(["uvicorn", "routers.app:app", "--host", "0.0.0.0", "--port", "8000"])

# def start_streamlit():
#     print("Starting Streamlit app...")
#     os.environ["PYTHONUNBUFFERED"] = "1"
#     subprocess.run(["streamlit", "run", "frontend/streamlit_app.py"])

# if __name__ == "__main__":
#     # Start FastAPI in a separate thread
#     api_thread = threading.Thread(target=start_fastapi, daemon=True)
#     api_thread.start()
    
#     # Wait for FastAPI to start
#     print("Waiting for FastAPI server to start...")
#     time.sleep(5)
    
#     # Start Streamlit app
#     start_streamlit()


import os
import subprocess
import threading
import time
import signal
import sys

# Global variables to track processes
fastapi_process = None
streamlit_process = None
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C and other termination signals."""
    print("\n\nReceived termination signal. Shutting down gracefully...")
    global running
    running = False
    cleanup()
    sys.exit(0)

def cleanup():
    """Clean up all running processes."""
    print("Cleaning up processes...")
    
    # Terminate Streamlit process
    if streamlit_process and streamlit_process.poll() is None:
        print("Terminating Streamlit process...")
        try:
            streamlit_process.terminate()
            # Wait a bit for graceful termination
            streamlit_process.wait(timeout=3)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            print("Forcing Streamlit process to exit...")
            streamlit_process.kill()
    
    # Terminate FastAPI process
    if fastapi_process and fastapi_process.poll() is None:
        print("Terminating FastAPI process...")
        try:
            fastapi_process.terminate()
            # Wait a bit for graceful termination
            fastapi_process.wait(timeout=3)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            print("Forcing FastAPI process to exit...")
            fastapi_process.kill()
    
    print("Cleanup complete")

def start_fastapi():
    """Start the FastAPI server as a subprocess."""
    global fastapi_process, running
    print("Starting FastAPI server...")
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # Use Popen instead of run to get a reference to the process
    fastapi_process = subprocess.Popen(
        ["uvicorn", "routers.app:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Monitor process output in a loop
    while running and fastapi_process.poll() is None:
        output = fastapi_process.stdout.readline()
        if output:
            print(f"[FastAPI] {output.strip()}")
    
    if running and fastapi_process.poll() is not None:
        print("FastAPI server stopped unexpectedly.")

def start_streamlit():
    """Start the Streamlit app as a subprocess."""
    global streamlit_process, running
    print("Starting Streamlit app...")
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # Use Popen instead of run to get a reference to the process
    streamlit_process = subprocess.Popen(
        ["streamlit", "run", "frontend/streamlit_app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Monitor process output in a loop
    while running and streamlit_process.poll() is None:
        output = streamlit_process.stdout.readline()
        if output:
            print(f"[Streamlit] {output.strip()}")
    
    if running and streamlit_process.poll() is not None:
        print("Streamlit app stopped unexpectedly.")
        running = False  # If Streamlit stops, we'll start shutdown

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        # Start FastAPI in a separate thread
        api_thread = threading.Thread(target=start_fastapi, daemon=True)
        api_thread.start()
        
        # Wait for FastAPI to start
        print("Waiting for FastAPI server to start...")
        time.sleep(5)
        
        # Start Streamlit in the main thread
        start_streamlit()
        
        # If we get here, Streamlit has exited
        print("Streamlit has exited. Initiating shutdown...")
        cleanup()
        
    except Exception as e:
        print(f"Error in main process: {e}")
        cleanup()
        sys.exit(1)