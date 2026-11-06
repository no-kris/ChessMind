import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.games import router as games_router
from app.api.routes import router

load_dotenv()

LOG_FORMAT = "%(levelname)-8s %(name)s: %(message)s"


def configure_logging(level_name: str) -> None:
    """Send the app's own loggers (app.*) to stderr at the given level.

    Configures the "app" logger, not the root logger, so it works the same under
    uvicorn (which configures only its own loggers) and under pytest (which adds
    root handlers that make logging.basicConfig a silent no-op).
    """
    level = logging.getLevelNamesMapping().get(level_name.upper())
    if level is None:
        raise ValueError(
            f"configure logging failed: LOG_LEVEL={level_name!r} is not a logging level; "
            "expected one of DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )
    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        app_logger.addHandler(handler)


configure_logging(os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(
    title="ChessMind backend API",
    version="0.0.1",
    description="Backend API for creating REST requests to Stockfish engine and OpenAI SDK",
)

ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422s with a string detail, like every other error, so clients handle one shape.

    Lists each bad field and the problem, but never echoes the submitted values.
    """
    problems = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": (
                f"{request.method} {request.url.path} failed: invalid request ({problems}); "
                "expected a request matching the API schema at /docs"
            )
        },
    )


app.include_router(router)
app.include_router(games_router)


@app.get("/")
async def root():
    return {"message": "ChessMind API up and running."}
