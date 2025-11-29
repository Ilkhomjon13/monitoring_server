from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
templates = Jinja2Templates(directory="templates")
pool: asyncpg.pool.Pool = None

# DB poolni ishga tushiramiz
@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)

@app.get("/monitor", response_class=HTMLResponse)
async def monitor_page(request: Request, survey_id: int):
    # Faqat sahifani yuboradi, ma’lumotni JS fetch qiladi
    return templates.TemplateResponse("monitor.html", {"request": request, "survey_id": survey_id})

@app.get("/monitor/data/{survey_id}")
async def monitor_data(survey_id: int):
    async with pool.acquire() as conn:
        survey = await conn.fetchrow("SELECT * FROM surveys WHERE id=$1", survey_id)
        candidates = await conn.fetch("SELECT name, votes FROM candidates WHERE survey_id=$1 ORDER BY id", survey_id)
    if not survey:
        return JSONResponse({"error": "Survey not found"}, status_code=404)
    data = {
        "survey": dict(survey),
        "candidates": [dict(c) for c in candidates]
    }
    return data
