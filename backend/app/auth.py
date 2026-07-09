import hashlib

from fastapi import HTTPException, Request, Response

from .config import settings

COOKIE_NAME = "admin_token"


def admin_token() -> str:
    return hashlib.sha256(f"fce-admin:{settings.admin_password}".encode()).hexdigest()


def login(response: Response, password: str) -> None:
    if password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid password")
    response.set_cookie(COOKIE_NAME, admin_token(), httponly=True, samesite="lax")


def require_admin(request: Request) -> None:
    token = request.cookies.get(COOKIE_NAME)
    bearer = request.headers.get("Authorization", "")
    if token == admin_token():
        return
    if bearer == f"Bearer {settings.admin_password}":
        return
    raise HTTPException(status_code=401, detail="Admin authentication required")
