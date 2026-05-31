from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.database import test_connection
from app.router import auth, dashboard, drafts



# Create FastAPI app
app = FastAPI(
    title="AI Social Media Automation Platform",
    description="Create, repurpose, approve and schedule content with AI",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Register routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(drafts.router)


# Test database on startup
@app.on_event("startup")
async def startup_event():
    print("Starting AI Social Media Platform...")
    test_connection()

# Landing page route
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

# Health check
@app.get("/health")
def health_check():
    return {"status": "running"}