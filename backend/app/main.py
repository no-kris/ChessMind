import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(override=True)

app = FastAPI(
    title="ChessMind backend API",
    version="0.0.1",
    description="Backend API for creating REST requests to Stockfish engine and OpenAI SDK",
)

ORIGINS = os.getenv("origins", "http://localhost:8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "ChessMind API up and running."}

@app.get("/analyze")
async def analyze():
    return {"message": "Frontend can talk to backend."}
