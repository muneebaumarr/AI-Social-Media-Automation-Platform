from fastapi import APIRouter, Depends, Request
from fastapi.responses    import RedirectResponse, JSONResponse
from fastapi.templating   import Jinja2Templates
from sqlalchemy.orm       import Session

from app.database         import get_db
from app.services.auth_service import get_optional_user, get_current_user
from app.services.ai_service   import generate_weekly_recommendation
from app.models.analytics     import (
    get_overview_stats, get_engagement_by_platform, get_status_breakdown,
    get_top_posts, get_latest_recommendation, save_recommendation,
)

router    = APIRouter(tags=["Analytics"])
templates = Jinja2Templates(directory="app/templates")


# PAGE ROUTE

@router.get("/analytics")
def analytics_page(request: Request, db: Session = Depends(get_db)):
    """
    Main analytics dashboard.
    Shows engagement stats, charts, top posts, and AI recommendation.
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    user_id = user["user_id"]

    overview        = get_overview_stats(db, user_id)
    platform_stats  = get_engagement_by_platform(db, user_id)
    status_data     = get_status_breakdown(db, user_id)
    top_posts       = get_top_posts(db, user_id, limit=5)
    recommendation  = get_latest_recommendation(db, user_id)

    # Find best platform for the badge
    best_platform = "None yet"
    if platform_stats:
        best_platform = platform_stats[0]["platform"].title()

    return templates.TemplateResponse("dashboard/analytics.html", {
        "request":         request,
        "user":            user,
        "overview":        overview,
        "platform_stats":  platform_stats,
        "status_data":     status_data,
        "top_posts":       top_posts,
        "best_platform":   best_platform,
        "recommendation":  recommendation,
    })


# API ROUTE — Generate fresh AI recommendation

@router.post("/api/analytics/generate-recommendation")
def generate_recommendation_api(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Calls Gemini to generate a fresh recommendation based on current analytics.
    Saves it to the database.
    """
    user = get_current_user(request)
    user_id = user["user_id"]

    # Get fresh analytics
    overview       = get_overview_stats(db, user_id)
    platform_stats = get_engagement_by_platform(db, user_id)

    # Find user's first client to attach this recommendation to
    from sqlalchemy import text
    client_row = db.execute(text("""
        SELECT DISTINCT client_id FROM content_drafts
        WHERE created_by = :uid LIMIT 1
    """), {"uid": user_id}).mappings().first()

    if not client_row:
        return JSONResponse(
            {"success": False, "error": "Create a draft first"},
            status_code=400,
        )

    # Call Gemini
    result = generate_weekly_recommendation(
        platform_stats=platform_stats,
        total_posts=overview["total_posts"],
    )

    # Save to database
    save_recommendation(
        db,
        client_id=client_row["client_id"],
        best_platform=result["best_platform"],
        recommendation_text=result["recommendation_text"],
    )

    return JSONResponse({
        "success": True,
        "best_platform":       result["best_platform"],
        "recommendation_text": result["recommendation_text"],
    })