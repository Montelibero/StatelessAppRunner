from fastapi import HTTPException

from db import get_user_by_key


def get_current_user_by_key(key: str, default_secret: str) -> dict:
    user = get_user_by_key(key)
    if not user:
        if key == default_secret:
            return {"id": 1, "key": default_secret, "comment": "Admin (Fallback)"}
        raise HTTPException(status_code=403, detail="Invalid Key")
    if user.get("id") != 1 and int(user.get("is_active", 1)) != 1:
        raise HTTPException(status_code=403, detail="User is banned")
    return user
