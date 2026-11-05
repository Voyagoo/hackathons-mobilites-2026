"""FastAPI app serving the dataviz. Run: uv run uvicorn app.main:app --reload"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_DIR      = Path(__file__).resolve().parent
TEMPLATE_DIR = APP_DIR / "templates"
STATIC_DIR   = APP_DIR / "static"

app       = FastAPI(title="Hackaviz 2026")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
