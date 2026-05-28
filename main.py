from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import test_connection


app = FastAPI(

    title="AI Social Media Automation Platform",
    description="Create, repurpose, approve and schedule content with AI",
    version="1.0.0",

)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

#test database connection on startup

@app.on_event("startup")
async def startup_event():
    print("Starting AI social media automation platform...")
    test_connection()

@app.get("/Health")
async def health_check():
    return {"status": "running",
             "message": "AI Social Media Automation Platform is running!",
             "version": "1.0.0"}

