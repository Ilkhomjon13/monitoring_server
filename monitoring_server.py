from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import databases

DATABASE_URL = "sqlite:///./test.db"  # yoki sizning real DB URL
database = databases.Database(DATABASE_URL)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Survey ma'lumotlarini olish
async def get_survey_by_id(survey_id: int):
    query = "SELECT id, short_title, description FROM surveys WHERE id = :survey_id"
    survey = await database.fetch_one(query=query, values={"survey_id": survey_id})
    if survey:
        return {"id": survey["id"], "short_title": survey["short_title"], "description": survey["description"]}
    return None

# Nomzodlar va ularning ovozlarini olish
async def get_candidates_by_survey(survey_id: int):
    query = "SELECT id, name, votes FROM candidates WHERE survey_id = :survey_id"
    rows = await database.fetch_all(query=query, values={"survey_id": survey_id})
    return [{"id": r["id"], "name": r["name"], "votes": r["votes"]} for r in rows]

# Monitor sahifasi
@app.get("/monitor")
async def monitor_page(request: Request, survey_id: int):
    survey = await get_survey_by_id(survey_id)
    if not survey:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Survey with id={survey_id} not found."},
            status_code=404
        )
    candidates = await get_candidates_by_survey(survey_id)
    return templates.TemplateResponse(
        "monitor.html",
        {
            "request": request,
            "survey": survey,
            "candidates": candidates,
            "survey_id": survey_id
        }
    )

# AJAX endpoint (grafikni yangilash)
@app.get("/monitor_data")
async def monitor_data(survey_id: int):
    candidates = await get_candidates_by_survey(survey_id)
    return JSONResponse(candidates)

# DBga ulanish/uzilish
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
