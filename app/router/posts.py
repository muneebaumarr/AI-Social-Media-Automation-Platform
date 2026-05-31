from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses    import RedirectResponse, JSONResponse
from fastapi.templating   import Jinja2Templates
from sqlalchemy.orm       import Session
from datetime             import datetime

from app.database         import get_db
from app.services.auth_service import get_optional_user, get_current_user
from app.models.post      import (
    get_posts_with_schedule_for_user, get_post_by_id, update_post_status,
)
from app.models.schedule  import create_schedule, get_schedule_by_post

router    = APIRouter(tags=["Posts"])
templates = Jinja2Templates(directory="app/templates")


# PAGE ROUTE — Posts list with filtering


@router.get("/posts")
def posts_page(request: Request, db: Session = Depends(get_db)):
    """
    Shows all posts created by the logged-in user.
    Includes scheduling info and latest manager remarks.
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    posts = get_posts_with_schedule_for_user(db, user["user_id"])

    return templates.TemplateResponse("dashboard/posts.html", {
        "request": request,
        "user":    user,
        "posts":   posts,
    })



# API ROUTE — Schedule a post


@router.post("/api/posts/{post_id}/schedule")
def schedule_post(
    post_id:        str,
    request:        Request,
    scheduled_time: str  = Form(...),  # ISO format: 2026-06-15T14:30
    db: Session = Depends(get_db),
):
    """
    Schedules an approved post for future publication.
    Only works on posts with status='approved'.
    """
    user = get_current_user(request)

    # ─── 1. Verify post exists and belongs to user ──────
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # ─── 2. Only approved posts can be scheduled ────────
    if post["status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot schedule a post with status '{post['status']}'. Must be 'approved'.",
        )

    # ─── 3. Prevent double scheduling ───────────────────
    existing = get_schedule_by_post(db, post_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="This post is already scheduled",
        )

    # ─── 4. Validate the time is in the future ──────────
    try:
        sched_dt = datetime.fromisoformat(scheduled_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if sched_dt <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Scheduled time must be in the future",
        )

    # ─── 5. Save the schedule + update post status ──────
    schedule_id = create_schedule(db, post_id, scheduled_time)
    update_post_status(db, post_id, "scheduled")

    return JSONResponse({
        "success":        True,
        "schedule_id":    schedule_id,
        "scheduled_time": scheduled_time,
        "message":        "Post scheduled successfully",
    })