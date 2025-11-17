# app/main.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from .config import SECRET, TIMEOUT_SECONDS
from .worker import solve_single_quiz
import asyncio
import uvicorn
import time

app = FastAPI(title="LLM Analysis Quiz Solver")

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

@app.post("/solve")
async def solve(req: QuizRequest):
    if req.secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    # enforce overall timeout (TIMEOUT_SECONDS)
    try:
        coro = solve_single_quiz(req.email, req.secret, req.url)
        res = await asyncio.wait_for(coro, timeout=TIMEOUT_SECONDS)
        return {"status": "done", "result": res}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: exceeded allowed time")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health
@app.get("/health")
def health():
    return {"status": "ok", "timeout_seconds": TIMEOUT_SECONDS}

# Run locally
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
