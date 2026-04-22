"""
Fast API backend for the Cover Letter Builder AI application. This module defines the API endpoints for generating cover letters, downloading generated documents, and handling WebSocket connections for real-time logging. It also includes a connection manager to manage active WebSocket connections and broadcast messages to connected clients. The backend interacts with the service module to perform the actual letter generation logic and uses the config module to load default configuration values.

Author: Sarvesh Telang
"""
import os
from typing import Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import asyncio

from config import get_default_config
from service import generate_letter


# =========================
# Connection Manager
# =========================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        dead_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"[WS ERROR] removing dead connection: {e}")
                dead_connections.append(connection)

        for conn in dead_connections:
            self.disconnect(conn)


# =========================
# App Setup
# =========================
app = FastAPI()
manager = ConnectionManager()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)


# =========================
# Request Model
# =========================
class RequestLetterService(BaseModel):
    ACCESS_KEY: Optional[str] = None
    FIRM: Optional[str] = None
    LOCATION: Optional[str] = None
    POSITION: Optional[str] = None
    JOB_DESCRIPTION: Optional[str] = None
    GREETING: Optional[str] = None
    BODY_WORD_COUNT: Optional[str] = None
    TIMEZONE: Optional[str] = None
    OUTPUT_FILE_NAME: Optional[str] = None
    TEMPLATE_PATH: Optional[str] = None
    LIBREOFFICE_PATH: Optional[str] = None


# =========================
# Routes
# =========================
@app.get("/defaults")
def get_defaults():
    return get_default_config()


@app.post("/generate")
async def generate(data: RequestLetterService):
    config = get_default_config()
    user_data = data.model_dump(exclude_unset=True)
    config.update(user_data)

    with open("src/banner.txt", "r", encoding="utf-8") as f:
        banner = f.read().rstrip()

    message = f"{banner}\n\n🚀 Starting letter generation..."
    await manager.broadcast(message)

    try:
        await manager.broadcast("📄 Generating document...")

        pdf_file, docx_file = await generate_letter(
            config,
            log=manager.broadcast
        )

        await manager.broadcast("✅ Done !!!")

    except Exception as e:
        print(f"[ERROR] {e}")
        await manager.broadcast("❌ Error occurred during generation")

        raise HTTPException(
            status_code=500,
            detail="An error occurred during cover letter generation"
        )

    return FileResponse(
        path=pdf_file,
        filename=config.get("OUTPUT_FILE_NAME", "output.pdf"),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{config.get("OUTPUT_FILE_NAME", "output.pdf")}.pdf"'
        }
    )


@app.get("/download/docx")
async def download_docx():
    file_path = output_dir / "main.docx"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename="main.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# =========================
# WebSocket Endpoint
# =========================
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        # Keep connection alive without blocking
        while True:
            await asyncio.sleep(40)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as e:
        print(f"[WS ERROR] {e}")
        manager.disconnect(websocket)