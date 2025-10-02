import uvicorn
import webbrowser
import threading
import time
import socket
from app.main import app

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0
    
def run():
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    if is_port_in_use(8000): # assume server already running
        webbrowser.open("http://127.0.0.1:8000")
    else:
        t = threading.Thread(target=run, daemon=True)
        t.start()
        time.sleep(3)
        webbrowser.open("http://127.0.0.1:8000")

    # keep main thread alive until ctrl+c or window close
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down.")
