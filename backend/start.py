import threading, time, webbrowser, uvicorn
from app.main import app

def run_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    app.state.server = server
    server.run()

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=False)
    t.start()
    time.sleep(0.6)
    webbrowser.open("http://127.0.0.1:8000")
    t.join()
