# Pipeline

Owns end-to-end orchestration across frame selection, COLMAP CUDA, splat training, export, and web validation.

Target responsibilities:

- Define job manifests.
- Track stages and retry boundaries.
- Keep training logs and metrics consistent across Splatfacto and fallback trainers.
- Produce scene records consumed by the web viewer.

Current orchestration lives in `apps/api/app/services/job_runner.py`.
