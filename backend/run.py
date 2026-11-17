"""
Launcher for Urvi Cairn Barmer FastAPI server.
"""

import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", 8002)))
    print(f"[*] Starting Urvi Cairn Barmer Backend on http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=False, ws_ping_interval=20)
