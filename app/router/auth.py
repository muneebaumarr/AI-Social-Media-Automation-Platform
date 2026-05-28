from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import get_user_by_email, create_user
from app.services.auth_service import (
    hash_password, verify_password, create_access_token,
)
from fastapi import Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix = "/auth", tags=["auth"])

@router.post("/register")
def register(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("Writer"),
    db: Session = Depends(get_db)

):
    
    """
    Registers a new user.

    1. Check if email already exists
    2. Hash the password
    3. Save the user

    """
    existing = get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(password)
    create_user(db, full_name, email, hashed_password, role)

    return JSONResponse(content={"message": "User registered successfully"}, status_code=201)   

@router.post("/login")
def login(
    email:    str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Logs a user in.
    1. Find user by email
    2. Verify password
    3. Create a JWT token
    4. Store token in a cookie
    """
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create token with user info
    token = create_access_token({
        "user_id": user["user_id"],
        "email":   user["email"],
        "role":    user["role"],
        "name":    user["full_name"],
    })

    # Store token in cookie and redirect to dashboard
    response = JSONResponse({
        "message": "Login successful",
        "role":    user["role"],
        "name":    user["full_name"],
    })
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
    )
    return response


@router.get("/logout")
def logout():
    """
    Logs the user out by deleting their cookie.
    """
    response = RedirectResponse(url="/auth/login-page")
    response.delete_cookie("access_token")
    return response

templates = Jinja2Templates(directory="app/templates")


@router.get("/login-page")
def login_page(request: Request):
    """Serves the HTML login page."""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register-page")
def register_page(request: Request):
    """Serves the HTML register page."""
    return templates.TemplateResponse("auth/register.html", {"request": request})