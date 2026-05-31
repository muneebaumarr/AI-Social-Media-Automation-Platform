from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses    import RedirectResponse, JSONResponse
from fastapi.templating   import Jinja2Templates
from sqlalchemy.orm       import Session

from app.database         import get_db
from app.services.auth_service import get_optional_user, get_current_user
from app.models.approval  import create_approval
from app.models.post      import (
    get_posts_by_status, get_post_by_id, update_post_status,
)

router    = APIRouter(tags=["Approvals"])
templates = Jinja2Templates(directory="app/templates")


# PAGE ROUTE — Manager Review Queue

@router.get("/manager")
def manager_queue_page(request: Request, db: Session = Depends(get_db)):
    """
    Shows all posts pending approval.
    Only accessible by managers and admins.
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    # Role check
    if user["role"] not in ["manager", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only managers can access the review queue",
        )

    pending_posts = get_posts_by_status(db, "pending_approval")

    return templates.TemplateResponse("dashboard/manager.html", {
        "request": request,
        "user":    user,
        "posts":   pending_posts,
    })


# API ROUTE — Manager submits a decision

@router.post("/api/posts/{post_id}/approve")
def submit_approval(
    post_id:         str,
    request:         Request,
    approval_status: str  = Form(...),
    remarks:         str  = Form(""),
    db: Session = Depends(get_db),
):
    """
    Records a manager's decision and updates the post status.
    """
    user = get_current_user(request)

    # Role check
    if user["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Only managers can approve posts")

    # Validate status
    if approval_status not in ["approved", "rejected", "request_edit"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be approved, rejected, or request_edit",
        )

    # Verify post exists
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # ─── 1. Record the approval decision ────────────────
    create_approval(
        db,
        post_id         = post_id,
        manager_id      = user["user_id"],
        approval_status = approval_status,
        remarks         = remarks.strip() if remarks else None,
    )

    # ─── 2. Update the post status ──────────────────────
    update_post_status(db, post_id, approval_status)

    return JSONResponse({
        "success":     True,
        "post_id":     post_id,
        "new_status":  approval_status,
        "message":     f"Post {approval_status.replace('_', ' ')} successfully",
    })