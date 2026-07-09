from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import admin, events, submissions, tips, towns
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Fairfield County Events API", version="0.1.0", lifespan=lifespan)

for router in (events.router, towns.router, submissions.router, tips.router, admin.router):
    app.include_router(router, prefix="/api/v1")


@app.get("/healthz")
def healthz():
    return {"ok": True}
