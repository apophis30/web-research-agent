import os
import subprocess
import threading
import time
import signal
import sys

# Global variables to track processes
fastapi_process = None
nextjs_process = None
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
    
    # Terminate Next.js process
    if nextjs_process and nextjs_process.poll() is None:
        print("Terminating Next.js process...")
        try:
            nextjs_process.terminate()
            # Wait a bit for graceful termination
            nextjs_process.wait(timeout=3)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            print("Forcing Next.js process to exit...")
            nextjs_process.kill()
    
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

def start_nextjs():
    """Start the Next.js app as a subprocess."""
    global nextjs_process, running
    print("Starting Next.js app...")
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # Store the original directory
    original_dir = os.getcwd()
    
    # Change to the frontend-next directory
    nextjs_dir = os.path.join(original_dir, "frontend/masonry-frontend-next")
    if not os.path.exists(nextjs_dir):
        print(f"Error: frontend-next directory not found at {nextjs_dir}")
        return
    
    # Check if package.json exists
    package_json = os.path.join(nextjs_dir, "package.json")
    if not os.path.exists(package_json):
        print(f"Error: package.json not found in {nextjs_dir}")
        return
    
    try:
        # Change to the Next.js directory
        os.chdir(nextjs_dir)
        print(f"Changed to directory: {os.getcwd()}")
        
        # Use Popen instead of run to get a reference to the process
        nextjs_process = subprocess.Popen(
            ["npm", "run", "dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=nextjs_dir  # Explicitly set the working directory
        )
        
        # Monitor process output in a loop
        while running and nextjs_process.poll() is None:
            output = nextjs_process.stdout.readline()
            if output:
                print(f"[Next.js] {output.strip()}")
        
        if running and nextjs_process.poll() is not None:
            print("Next.js app stopped unexpectedly.")
            running = False  # If Next.js stops, we'll start shutdown
            
    except Exception as e:
        print(f"Error starting Next.js: {str(e)}")
        running = False
    finally:
        # Change back to the original directory
        os.chdir(original_dir)

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
        
        # Start Next.js in the main thread
        start_nextjs()
        
        # If we get here, Next.js has exited
        print("Next.js has exited. Initiating shutdown...")
        cleanup()
        
    except Exception as e:
        print(f"Error in main process: {e}")
        cleanup()
        sys.exit(1)