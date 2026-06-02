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


from app.models.social_account import (
    get_accounts_for_brand, connect_account, disconnect_account,
)


router    = APIRouter(tags=["Brands"])
templates = Jinja2Templates(directory="app/templates")


# BRAND LIST PAGE

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


# CREATE NEW BRAND

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


# BRAND DETAIL / EDIT PAGE


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


# JOIN A BRAND VIA INVITE CODE  (must be before /{client_id})


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



# SOCIAL ACCOUNTS PAGE

@router.get("/brands/{client_id}/accounts")
def brand_accounts_page(client_id: str, request: Request,
                        db: Session = Depends(get_db)):
    """
    Page showing connected social accounts for a brand.
    Available to all brand members.
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/auth/login-page")

    brand = get_brand_by_id(db, client_id, user["user_id"])
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found or no access")

    accounts = get_accounts_for_brand(db, client_id)

    # Build a lookup so the template can easily check each platform
    connected_map = {a["platform"]: a for a in accounts if a["connected_status"]}

    platforms = [
        {"key": "instagram", "name": "Instagram",
         "color": "#E1306C",
         "icon": "M16,5h-8a3,3 0 0,0 -3,3v8a3,3 0 0,0 3,3h8a3,3 0 0,0 3,-3v-8a3,3 0 0,0 -3,-3zM12,15a3,3 0 1,1 0,-6 3,3 0 0,1 0,6z"},
        {"key": "linkedin",  "name": "LinkedIn",
         "color": "#0A66C2",
         "icon": "M4.98,3.5C4.98,4.881 3.87,6 2.5,6S0.02,4.881 0.02,3.5C0.02,2.12 1.13,1 2.5,1S4.98,2.12 4.98,3.5zM0,8h5v16h-5V8zM7.982,8H12.9v2.41h0.07c0.68,-1.29 2.345,-2.65 4.825,-2.65c5.16,0 6.11,3.39 6.11,7.8V24h-5.1v-7.55c0,-1.8 -0.03,-4.12 -2.51,-4.12c-2.51,0 -2.895,1.96 -2.895,3.99V24h-5.097V8z"},
        {"key": "twitter",   "name": "Twitter / X",
         "color": "#000000",
         "icon": "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"},
        {"key": "facebook",  "name": "Facebook",
         "color": "#1877F2",
         "icon": "M24 12.073c0,-6.627 -5.373,-12 -12,-12s-12,5.373 -12,12c0,5.99 4.388,10.954 10.125,11.854v-8.385H7.078v-3.47h3.047V9.43c0,-3.007 1.792,-4.669 4.533,-4.669c1.312,0 2.686,0.235 2.686,0.235v2.953H15.83c-1.491,0 -1.956,0.925 -1.956,1.874v2.25h3.328l-0.532,3.47h-2.796v8.385C19.612,23.027 24,18.062 24,12.073z"},
        {"key": "tiktok",    "name": "TikTok",
         "color": "#000000",
         "icon": "M19.59,6.69a4.83,4.83 0 0,1 -3.77,-4.25V2h-3.45v13.67a2.89,2.89 0 0,1 -5.2,1.74 2.89,2.89 0 0,1 2.31,-4.64 2.93,2.93 0 0,1 0.88,0.13V9.4a6.84,6.84 0 0,0 -1,-0.05A6.33,6.33 0 0,0 5.8,20.1a6.34,6.34 0 0,0 10.86,-4.43v-7a8.16,8.16 0 0,0 4.77,1.52v-3.4a4.85,4.85 0 0,1 -1.84,-0.1z"},
        {"key": "youtube",   "name": "YouTube",
         "color": "#FF0000",
         "icon": "M23.498,6.186a3.016,3.016 0 0,0 -2.122,-2.136C19.505,3.545 12,3.545 12,3.545s-7.505,0 -9.377,0.505A3.017,3.017 0 0,0 0.502,6.186C0,8.07 0,12 0,12s0,3.93 0.502,5.814a3.016,3.016 0 0,0 2.122,2.136c1.871,0.505 9.376,0.505 9.376,0.505s7.505,0 9.377,-0.505a3.015,3.015 0 0,0 2.122,-2.136C24,15.93 24,12 24,12s0,-3.93 -0.502,-5.814zM9.545,15.568V8.432L15.818,12l-6.273,3.568z"},
    ]

    return templates.TemplateResponse("dashboard/brand_accounts.html", {
        "request":       request,
        "user":          user,
        "brand":         brand,
        "platforms":     platforms,
        "connected_map": connected_map,
        "can_edit":      brand["access_type"] == "owner",
    })


@router.post("/api/brands/{client_id}/accounts/connect")
def connect_account_api(
    client_id:    str,
    request:      Request,
    platform:     str  = Form(...),
    account_name: str  = Form(...),
    db: Session = Depends(get_db),
):
    """
    Connects a social account to a brand.
    Only the brand owner can connect accounts.
    """
    user = get_current_user(request)

    # Verify ownership
    brand = get_brand_by_id(db, client_id, user["user_id"])
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    if brand["access_type"] != "owner":
        raise HTTPException(
            status_code=403,
            detail="Only the brand owner can connect accounts",
        )

    # Validate platform
    valid_platforms = {"instagram", "linkedin", "twitter",
                       "facebook", "tiktok", "youtube"}
    if platform not in valid_platforms:
        raise HTTPException(status_code=400, detail="Invalid platform")

    # Validate account name
    handle = account_name.strip().lstrip("@")
    if len(handle) < 2:
        raise HTTPException(status_code=400, detail="Handle too short")

    account_id = connect_account(db, client_id, platform, f"@{handle}")

    return JSONResponse({
        "success":    True,
        "account_id": account_id,
        "platform":   platform,
        "handle":     f"@{handle}",
        "message":    f"{platform.title()} connected successfully",
    })


@router.post("/api/brands/{client_id}/accounts/disconnect")
def disconnect_account_api(
    client_id:    str,
    request:      Request,
    platform:     str  = Form(...),
    db: Session = Depends(get_db),
):
    """
    Disconnects a social account.
    Only the brand owner can disconnect.
    """
    user = get_current_user(request)

    brand = get_brand_by_id(db, client_id, user["user_id"])
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    if brand["access_type"] != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can disconnect")

    disconnect_account(db, client_id, platform)

    return JSONResponse({
        "success": True,
        "message": f"{platform.title()} disconnected",
    })