# COLMAP CUDA

Owns sparse reconstruction on NVIDIA GPU hosts.

Target responsibilities:

- Run CUDA SIFT feature extraction.
- Run CUDA sequential matching.
- Run incremental mapping with tuned bundle adjustment settings.
- Export COLMAP artifacts in the layout expected by Splatfacto and OpenSplat CUDA fallback paths.

Current implementation is still inside `apps/api/app/services/colmap_runner.py`.
