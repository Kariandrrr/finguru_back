import os, json, hmac, hashlib
import time
from urllib.parse import parse_qsl

from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

def validate_init_data(init_data: str, max_age: int = 3600) -> dict | None:
    data = dict(parse_qsl(init_data, keep_blank_values=True))

    got_hash = data.pop("hash", "")
    if not got_hash:
        raise HTTPException(status_code=400, detail="Hash is required")

    try:
        auth_date = int(data["auth_date"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Auth date is required")

    current_time = int(time.time())
    if current_time - auth_date > max_age:
        raise HTTPException(status_code=403, detail="Init data expired")

    data_check_string = "\n".join(
        f"{k}={data[k]}" for k in sorted(
            data.keys()
            )
        )

    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, got_hash):
        raise HTTPException(status_code=400, detail="Hash is invalid")

    user_str = data.get("user")
    if user_str:
        return json.loads(user_str)
    return None


@router.post("/tg/auth")
async def auth(req: Request):
    body = await req.json()
    user = validate_init_data(body.get("initData", ""))

    if not user:
        raise HTTPException(status_code=401, detail="Invalid initData")

    first_name = (user.get("first_name", "") or "").strip()
    last_name = (user.get("last_name", "") or "").strip()
    full_name = (first_name + " " + last_name).strip() or "friend"

    return {
        "ok": True,
        "full_name": full_name,
    }

