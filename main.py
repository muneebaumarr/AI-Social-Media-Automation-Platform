from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.database import test_connection
from app.router import auth, dashboard, drafts, approvals, posts, analytics, brands


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        test_connection()
        print("DB connected")
    except Exception as e:
        print("DB connection failed:", e)
    yield


app = FastAPI(
    title="AI Social Media Automation Platform",
    description="Create, repurpose, approve and schedule content with AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
#app.mount("/static", StaticFiles(directory="app/static"), name="static")

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Register routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(drafts.router)
app.include_router(approvals.router)
app.include_router(posts.router)
app.include_router(analytics.router)
app.include_router(brands.router)


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/health")
def health_check():
    return {"status": "running"}
