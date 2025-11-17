# app/utils.py
import asyncio
import json
from typing import Any

def now_ms():
    import time
    return int(time.time() * 1000)

def safe_json(d):
    try:
        return json.dumps(d)
    except Exception:
        return str(d)
