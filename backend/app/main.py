from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import JOBS_DIR, SCENES_DIR

app = FastAPI(title="3DGS OpenSplat MVP")

JOBS_DIR.mkdir(parents=True, exist_ok=True)
SCENES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static/jobs", StaticFiles(directory=JOBS_DIR), name="jobs-static")
app.mount("/static/scenes", StaticFiles(directory=SCENES_DIR), name="scenes-static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
