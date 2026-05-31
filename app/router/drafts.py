from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.services.ai_service import repurpose_for_platforms

from app.database import get_db
from app.services.auth_service import get_current_user, get_optional_user
from app.models.draft import create_draft, get_draft_by_id, get_drafts_by_user, update_draft_status

from app.models.post import create_post, save_ai_generation

from app.models.user import get_all_clients


router = APIRouter(tags=["drafts"])
templates = Jinja2Templates(directory = "app/templates")


# Page Routes 

@router.get("/drafts")
def drafts_list_page(request: Request, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    shows a list of all drafts created by the logged-in user. Each draft entry includes the title, associated client, creation date, and current status. Users can click on a draft to view its details or edit it.
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url = "/auth/login-page")
    
    drafts = get_drafts_by_user(db, user["user_id"])
    return templates.TemplateResponse("dashboard/drafts.html", {
        "request": request,
        "user" : user,
        "drafts": drafts,
    })


@router.get("/drafts/new")
def new_draft_page(request: Request, db: Session = Depends(get_db)):
    """
    Shows the form to create a new draft.
    User picks a client, writes content, selects platforms.
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    clients = get_all_clients(db)

    return templates.TemplateResponse("dashboard/new_draft.html", {
        "request": request,
        "user":    user,
        "clients": clients,
    })



@router.post("/api/drafts")
def create_draft_api(
    request:      Request,
    client_id:    str       = Form(...),
    draft_title:  str       = Form(...),
    draft_content: str      = Form(...),
    db: Session = Depends(get_db),
):
    """
    Creates a new draft in the database.
    Called by the new draft page via fetch().
    """
    user = get_current_user(request)

    # Basic validation
    if len(draft_title.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Draft title must be at least 3 characters",
        )

    if len(draft_content.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Draft content must be at least 20 characters",
        )

    # Save draft
    draft_id = create_draft(
        db,
        client_id     = client_id,
        created_by    = user["user_id"],
        draft_title   = draft_title.strip(),
        draft_content = draft_content.strip(),
    )

    return JSONResponse({
        "success":  True,
        "draft_id": draft_id,
        "message":  "Draft saved successfully",
    })


@router.post("/api/repurpose")
def repurpose_draft_api(
    request:   Request,
    draft_id:  str       = Form(...),
    platforms: str       = Form(...),   # comma-separated string
    db: Session = Depends(get_db),
):
    """
    Sends the draft to Gemini AI for repurposing.
    Saves the generated posts to the database.
    Returns the list of created posts.
    """
    user = get_current_user(request)

    # Parse platforms from comma-separated string
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    if not platform_list:
        raise HTTPException(
            status_code=400,
            detail="At least one platform must be selected",
        )

    # Verify draft exists and belongs to this user
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft["created_by"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your draft")

    # ─── Call Gemini AI ────────────────────────────────────
    results = repurpose_for_platforms(
        draft_title   = draft["draft_title"],
        draft_content = draft["draft_content"],
        platforms     = platform_list,
    )

    # ─── Save each generated post to DB ─────────────────────
    saved_posts = []
    for r in results:
        if not r.get("success"):
            continue   # Skip failed generations

        # Save the AI generation record (audit trail)
        save_ai_generation(
            db,
            draft_id       = draft_id,
            platform       = r["platform"],
            prompt         = r.get("prompt", ""),
            generated_text = r.get("repurposed_content", ""),
        )

        # Save the post itself
        post_id = create_post(
            db,
            draft_id           = draft_id,
            platform           = r["platform"],
            repurposed_content = r.get("repurposed_content", ""),
            caption            = r.get("caption", ""),
            hashtags           = r.get("hashtags", ""),
        )

        saved_posts.append({
            "post_id":            post_id,
            "platform":           r["platform"],
            "repurposed_content": r.get("repurposed_content", ""),
            "caption":            r.get("caption", ""),
            "hashtags":           r.get("hashtags", ""),
        })

    if not saved_posts:
        errors = [r.get("error", "unknown error") for r in results if not r.get("success")]
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed for all platforms. Errors: {'; '.join(errors)}",
        )

    # Update draft status
    update_draft_status(db, draft_id, "repurposed")

    return JSONResponse({
        "success":       True,
        "post_count":    len(saved_posts),
        "posts":         saved_posts,
    })