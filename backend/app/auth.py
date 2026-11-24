"""כניסת מנהלת.

אחרי שהסיסמה נכונה, השרת מחזיר "כרטיס כניסה" (token) חתום עם SECRET_KEY.
הדפדפן שולח את הכרטיס בכל פעולה של מנהלת, והשרת בודק שהחתימה נכונה ושהוא לא פג.
"""
import base64
import hashlib
import hmac
import time

from fastapi import Header, HTTPException, status

from .config import ADMIN_PASSWORD, SECRET_KEY, TOKEN_HOURS


def _sign(payload: str) -> str:
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def check_password(password: str) -> bool:
    if not ADMIN_PASSWORD or not SECRET_KEY:
        return False
    return hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode())


def make_token() -> str:
    expires = int(time.time()) + TOKEN_HOURS * 3600
    payload = f"admin.{expires}"
    return f"{payload}.{_sign(payload)}"


def require_admin(authorization: str = Header(default="")) -> None:
    """נכנס לכל נתיב של מנהלת. אם אין כרטיס תקף - מחזיר 401."""
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "צריך להתחבר מחדש")
    if not SECRET_KEY or not authorization.startswith("Bearer "):
        raise unauthorized
    token = authorization[len("Bearer "):]
    try:
        role, expires, sig = token.split(".")
    except ValueError:
        raise unauthorized
    payload = f"{role}.{expires}"
    if role != "admin" or not hmac.compare_digest(sig, _sign(payload)):
        raise unauthorized
    if not expires.isdigit() or int(expires) < time.time():
        raise unauthorized
