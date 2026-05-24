# Viewer

Owns browser-side validation for generated 3DGS scenes.

Target responsibilities:

- Load generated Gaussian splat assets in the web UI.
- Provide camera controls, scene metadata, and visual sanity checks.
- Keep acceptance tied to actual browser rendering, not only file existence.

Current viewer HTML is served by `apps/api/app/routes/jobs.py`.
