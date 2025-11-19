# app/utils.py
import json

def now_ms():
    import time
    return int(time.time() * 1000)

def safe_json(d):
    try:
        return json.dumps(d)
    except Exception:
        return str(d)
