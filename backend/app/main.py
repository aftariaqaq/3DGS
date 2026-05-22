from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import JOBS_DIR, SCENES_DIR
from app.routes import jobs

app = FastAPI(title="3DGS OpenSplat MVP")

JOBS_DIR.mkdir(parents=True, exist_ok=True)
SCENES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static/jobs", StaticFiles(directory=JOBS_DIR), name="jobs-static")
app.mount("/static/scenes", StaticFiles(directory=SCENES_DIR), name="scenes-static")
app.include_router(jobs.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
