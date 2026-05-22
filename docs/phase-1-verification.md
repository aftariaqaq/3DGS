# Phase 1 Verification

## 2026-05-22 Command-Line Pipeline Smoke Test

Input video:

```text
D:\.codex_workplace\3DGS\test_video\VID_20260522_163140.mp4
```

Video properties:

```text
Resolution: 3840x2160
Frame rate: 30 fps
Duration: 61.549044 seconds
Codec: HEVC Main 10 / HDR Vivid
```

Environment:

```text
FFmpeg: OK
COLMAP nocuda Windows package: OK
OpenSplat: OK via local Docker image opensplat-cpu:local
```

Command:

```powershell
.\scripts\run_pipeline_test.ps1 `
  -InputVideo 'D:\.codex_workplace\3DGS\test_video\VID_20260522_163140.mp4' `
  -JobId 'job_test_video_004' `
  -Fps 1 `
  -MaxFrames 30 `
  -Iterations 50
```

Result:

```text
Pipeline complete
Frames: 30
Output: D:\.codex_workplace\3DGS\data\jobs\job_test_video_004\opensplat\splat.ply
```

Output files:

```text
D:\.codex_workplace\3DGS\data\jobs\job_test_video_004\opensplat\splat.ply
D:\.codex_workplace\3DGS\data\jobs\job_test_video_004\opensplat\cameras.json
```

Issues found and fixed:

- COLMAP `feature_extractor` crashed with the default GPU feature extraction path in the CPU/nocuda environment. Fixed by adding `--FeatureExtraction.use_gpu 0`.
- COLMAP `sequential_matcher` crashed with the default GPU matching path in the CPU/nocuda environment. Fixed by adding `--FeatureMatching.use_gpu 0` and `--SiftMatching.cpu_brute_force_matcher 1`.
- OpenSplat did not recognize the job root as a COLMAP project because COLMAP outputs live under `colmap/sparse/0` while images live under `images`. Fixed by invoking OpenSplat with `/work/colmap` and `--colmap-image-path /work/images`.

Notes:

- A manual OpenSplat run with `50` frames and `300` iterations also succeeded after correcting the OpenSplat input path, producing `splat.ply` and `cameras.json` for `job_test_video_003`.
- This verification covers the command-line pipeline only. The final Phase 1 acceptance still requires Web upload, job status, and browser-based 3DGS viewing.

