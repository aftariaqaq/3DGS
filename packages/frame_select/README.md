# Frame Selection

Owns video-to-frame preparation for the CUDA pipeline.

Target responsibilities:

- Extract candidate frames from phone or lightweight capture-app videos.
- Score blur, exposure, overlap, and motion spacing.
- Select a bounded training set before COLMAP.
- Persist selection metadata so training runs are reproducible.

`packages.pipeline.prepare_capture` owns the current host implementation. Android capture bundles and plain video imports both normalize into the same capture layout before selection. Plain video uses `process-video --no-sensors`, which derives frame timestamps from `ffprobe` and writes empty sensor streams.
