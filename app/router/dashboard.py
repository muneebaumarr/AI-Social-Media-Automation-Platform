from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.services.auth_service import get_optional_user

router    = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Main dashboard page.
    Shows stats and recent activity for the logged-in user.
    """
    # Check if logged in
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    user_id = user["user_id"]

    # ─── Fetch stats ──────────────────────────────────────
    # Total drafts created by this user
    total_drafts = db.execute(
        text("SELECT COUNT(*) FROM content_drafts WHERE created_by = :uid"),
        {"uid": user_id},
    ).scalar()

    # Total posts (across all users for now)
    total_posts = db.execute(text("SELECT COUNT(*) FROM posts")).scalar()

    # Posts pending approval
    pending_approval = db.execute(
        text("SELECT COUNT(*) FROM posts WHERE status = 'pending_approval'")
    ).scalar()

    # Posts that have been published
    published = db.execute(
        text("SELECT COUNT(*) FROM posts WHERE status = 'published'")
    ).scalar()

    # ─── Recent drafts (last 5) ───────────────────────────
    recent_drafts = db.execute(
        text("""
            SELECT cd.draft_id, cd.draft_title, cd.draft_status, cd.created_at,
                   c.client_name
            FROM content_drafts cd
            LEFT JOIN clients c ON c.client_id = cd.client_id
            WHERE cd.created_by = :uid
            ORDER BY cd.created_at DESC
            LIMIT 5
        """),
        {"uid": user_id},
    ).mappings().all()

    return templates.TemplateResponse("dashboard/dashboard.html", {
        "request":          request,
        "user":             user,
        "total_drafts":     total_drafts,
        "total_posts":      total_posts,
        "pending_approval": pending_approval,
        "published":        published,
        "recent_drafts":    recent_drafts,
    })