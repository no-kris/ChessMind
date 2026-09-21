from fastapi import FastAPI

app = FastAPI(
    title="ChessMind backend API",
    version="0.0.1",
    description="Backend API for creating REST requests to Stockfish engine and OpenAI SDK",
)


@app.get("/")
async def root():
    return {"message": "ChessMind API up and running."}
