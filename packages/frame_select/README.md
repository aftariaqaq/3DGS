# Frame Selection

Owns video-to-frame preparation for the CUDA pipeline.

Target responsibilities:

- Extract candidate frames from phone or lightweight capture-app videos.
- Score blur, exposure, overlap, and motion spacing.
- Select a bounded training set before COLMAP.
- Persist selection metadata so training runs are reproducible.

Current implementation is still inside `apps/api/app/services/ffmpeg_runner.py`; this package is the boundary for the next extraction step.
