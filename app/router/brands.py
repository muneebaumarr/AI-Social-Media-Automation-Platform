from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses    import RedirectResponse, JSONResponse
from fastapi.templating   import Jinja2Templates
from sqlalchemy.orm       import Session

from app.database         import get_db
from app.services.auth_service import get_optional_user, get_current_user
from app.models.brand     import (
    create_brand, get_brands_for_user, get_brand_by_id, update_brand,
    add_member_by_invite_code, get_brand_members,
)

router    = APIRouter(tags=["Brands"])
templates = Jinja2Templates(directory="app/templates")


# ═══════════════════════════════════════════════════════════
# BRAND LIST PAGE
# ═══════════════════════════════════════════════════════════

@router.get("/brands")
def brands_list_page(request: Request, db: Session = Depends(get_db)):
    """
    Shows all brands the user has access to.
    Admin: owned + member brands
    Writer/Manager: only member brands
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    brands = get_brands_for_user(db, user["user_id"], user["role"])

    return templates.TemplateResponse("dashboard/brands.html", {
        "request": request,
        "user":    user,
        "brands":  brands,
    })


# ═══════════════════════════════════════════════════════════
# CREATE NEW BRAND
# ═══════════════════════════════════════════════════════════

@router.get("/brands/new")
def new_brand_page(request: Request):
    """
    Brand creation wizard. Only admins can create brands.
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can create brands",
        )

    return templates.TemplateResponse("dashboard/new_brand.html", {
        "request": request,
        "user":    user,
    })


@router.post("/api/brands")
def create_brand_api(
    request:         Request,
    brand_name:      str       = Form(...),
    industry:        str       = Form(""),
    brand_voice:     str       = Form(""),
    target_audience: str       = Form(""),
    brand_color:     str       = Form("#0a0a0a"),
    do_not_use:      str       = Form(""),
    db: Session = Depends(get_db),
):
    """API endpoint to create a new brand."""
    user = get_current_user(request)

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create brands")

    if len(brand_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Brand name too short")

    client_id = create_brand(
        db,
        owner_id        = user["user_id"],
        brand_name      = brand_name.strip(),
        industry        = industry.strip() or None,
        brand_voice     = brand_voice.strip() or None,
        target_audience = target_audience.strip() or None,
        brand_color     = brand_color,
        do_not_use      = do_not_use.strip() or None,
    )

    return JSONResponse({
        "success":   True,
        "client_id": client_id,
        "message":   "Brand created successfully",
    })


# ═══════════════════════════════════════════════════════════
# BRAND DETAIL / EDIT PAGE
# ═══════════════════════════════════════════════════════════

@router.get("/brands/{client_id}")
def brand_detail_page(client_id: str, request: Request,
                      db: Session = Depends(get_db)):
    """
    Brand detail page. Shows brand info and members.
    Editable for owner, read-only for writers/managers.
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    brand = get_brand_by_id(db, client_id, user["user_id"])
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found or no access")

    members = get_brand_members(db, client_id)

    return templates.TemplateResponse("dashboard/brand_detail.html", {
        "request": request,
        "user":    user,
        "brand":   brand,
        "members": members,
        "can_edit": brand["access_type"] == "owner",
    })


@router.post("/api/brands/{client_id}")
def update_brand_api(
    client_id:       str,
    request:         Request,
    industry:        str  = Form(""),
    brand_voice:     str  = Form(""),
    target_audience: str  = Form(""),
    brand_color:     str  = Form("#0a0a0a"),
    do_not_use:      str  = Form(""),
    db: Session = Depends(get_db),
):
    """Updates brand details. Only owner can edit."""
    user = get_current_user(request)

    success = update_brand(
        db,
        client_id       = client_id,
        owner_id        = user["user_id"],
        industry        = industry.strip(),
        brand_voice     = brand_voice.strip(),
        target_audience = target_audience.strip(),
        brand_color     = brand_color,
        do_not_use      = do_not_use.strip(),
    )

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Only the brand owner can edit",
        )

    return JSONResponse({"success": True, "message": "Brand updated"})


# ═══════════════════════════════════════════════════════════
# JOIN A BRAND VIA INVITE CODE
# ═══════════════════════════════════════════════════════════

@router.post("/api/brands/join")
def join_brand_api(
    request:     Request,
    invite_code: str  = Form(...),
    db: Session = Depends(get_db),
):
    """Adds the user to a brand using the invite code."""
    user = get_current_user(request)

    result = add_member_by_invite_code(
        db, user_id=user["user_id"], invite_code=invite_code.strip(),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Invalid invite code",
        )

    if result["already_member"]:
        return JSONResponse({
            "success": True,
            "message": f"You're already a member of {result['client_name']}",
            "client_id": result["client_id"],
        })

    return JSONResponse({
        "success": True,
        "message": f"Joined {result['client_name']} successfully",
        "client_id": result["client_id"],
    })