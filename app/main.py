# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import SECRET, TIMEOUT_SECONDS
from .worker import solve_single_quiz
import asyncio
import uvicorn


app = FastAPI(title="LLM Analysis Quiz Solver")

@app.get("/")
def root():
    return {"status": "OK"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str


@app.post("/solve")
async def solve(req: QuizRequest):
    if req.secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    try:
        task = solve_single_quiz(req.email, req.secret, req.url)
        result = await asyncio.wait_for(task, timeout=TIMEOUT_SECONDS)

        return {
            "status": "ok",
            "timeout": TIMEOUT_SECONDS,
            "result": result,
        }

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Timeout: exceeded {TIMEOUT_SECONDS} seconds"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/health")
def health():
    return {"status": "ok", "timeout_seconds": TIMEOUT_SECONDS}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
