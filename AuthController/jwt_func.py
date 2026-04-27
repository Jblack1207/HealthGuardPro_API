import os
from datetime import datetime, timedelta, timezone
from jose import jwt
import uuid

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALG = os.getenv("JWT_ALG", "")

ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", ""))

def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def create_access_token(user_id: int, is_admin: bool) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not set")
    exp = now_utc() + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "is_admin": bool(is_admin),
        "exp": exp,
        "iat": now_utc(),
        "jti": jti,
        "type": "access"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token, jti, exp


import jwt
from jwt import ExpiredSignatureError, PyJWTError

def decode_access_token(token: str, *, verify_exp: bool = True) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALG],
            options={"verify_exp": verify_exp},
        )

        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Wrong token type")

        return payload

    except ExpiredSignatureError:
        raise

    except PyJWTError:
        raise

