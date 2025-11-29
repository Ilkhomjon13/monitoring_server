import os
import asyncpg
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# DB pool
pool = None

# WebSocket connections {survey_id: [websocket1, websocket2]}
active_connections = {}


@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)


@app.get("/monitor")
async def monitor_page(request: Request, survey_id: int):
    """
    Monitoring sahifa HTML
    """
    return templates.TemplateResponse(
        "monitor.html", 
        {"request": request, "survey_id": survey_id}
    )


@app.websocket("/ws/{survey_id}")
async def websocket_endpoint(websocket: WebSocket, survey_id: int):
    survey_id = int(survey_id)
    await websocket.accept()

    if survey_id not in active_connections:
        active_connections[survey_id] = []
    active_connections[survey_id].append(websocket)

    # Boshlang‘ich natijalarni yuborish
    await send_current_votes(survey_id, websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        active_connections[survey_id].remove(websocket)


async def send_current_votes(survey_id: int, websocket: WebSocket = None):
    """
    Yangi natijalarni WebSocket orqali yuboradi
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT name, votes FROM candidates WHERE survey_id=$1 ORDER BY id",
            survey_id
        )

    data = [{"name": r["name"], "votes": r["votes"]} for r in rows]

    message = {"type": "update", "data": data}

    # Bitta WSga yuborish
    if websocket:
        await websocket.send_json(message)
        return

    # Barcha WS klientlarga yuborish
    if survey_id in active_connections:
        for ws in active_connections[survey_id]:
            try:
                await ws.send_json(message)
            except:
                pass


@app.post("/notify_vote/{survey_id}")
async def notify_vote(survey_id: int):
    """
    BOT shu endpointga POST so‘rov yuboradi (yangi ovoz bo‘lganda)
    """
    await send_current_votes(survey_id)
    return {"status": "ok"}
