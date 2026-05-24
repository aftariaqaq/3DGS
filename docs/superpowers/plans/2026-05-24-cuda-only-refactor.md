# CUDA-Only Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the current OpenSplat CPU prototype into a clean CUDA-only 3DGS workspace centered on frame selection, CUDA COLMAP, Nerfstudio Splatfacto, and web validation.

**Architecture:** Move runnable applications under `apps/`, reusable workflow modules under `packages/`, and operational scripts under `scripts/ops`. Preserve the existing FastAPI viewer behavior while replacing CPU-first naming and script layout with CUDA-only boundaries.

**Tech Stack:** FastAPI, pytest, PowerShell operational scripts, Docker CUDA images, Python frame-selection and pipeline packages.

---

### Task 1: Workspace Hygiene

**Files:**
- Modify: `.gitignore`
- Delete local generated directories only: `data/`, `artifacts/`, `.pytest_cache/`

- [ ] **Step 1: Verify workspace paths**

Run: `Resolve-Path data,artifacts,.pytest_cache -ErrorAction SilentlyContinue`
Expected: every resolved path starts with `D:\.codex_workplace\3DGS`.

- [ ] **Step 2: Remove local generated directories**

Run: guarded PowerShell `Remove-Item -Recurse -Force` only for paths verified inside the workspace.
Expected: `data/`, `artifacts/`, and `.pytest_cache/` are gone. `test_video/` remains.

- [ ] **Step 3: Keep generated outputs ignored**

Ensure `.gitignore` includes `data/`, `captures/`, `artifacts/`, and `.pytest_cache/`.

### Task 2: Move API Into Apps Layout

**Files:**
- Move: `backend/` -> `apps/api/`
- Modify: `apps/api/app/config.py`
- Modify tests under `apps/api/tests/`

- [ ] **Step 1: Move backend tree**

Move the existing FastAPI package and tests to `apps/api/` without changing behavior.

- [ ] **Step 2: Update project root detection**

`apps/api/app/config.py` must resolve the repository root two levels above `apps/api/app`, so `DATA_DIR` still points at `<repo>/data`.

- [ ] **Step 3: Run API tests**

Run: `$env:PYTHONPATH='D:\.codex_workplace\3DGS\apps\api'; python -m pytest apps/api/tests`
Expected: all tests pass.

### Task 3: Create CUDA-Only Package Boundaries

**Files:**
- Create: `packages/frame_select/README.md`
- Create: `packages/colmap_cuda/README.md`
- Create: `packages/splatfacto/README.md`
- Create: `packages/pipeline/README.md`
- Create: `packages/viewer/README.md`

- [ ] **Step 1: Add package README files**

Each package README explains responsibility, inputs, outputs, and current implementation status.

- [ ] **Step 2: Keep first implementation minimal**

Do not implement full frame scoring yet. This refactor creates clear package boundaries and leaves behavior-preserving tests green.

### Task 4: Reorganize Operational Scripts

**Files:**
- Move: `scripts/build_opensplat_cuda_docker.ps1` -> `scripts/ops/build_opensplat_cuda_docker.ps1`
- Move: `scripts/run_opensplat_cuda_only.ps1` -> `scripts/ops/run_opensplat_cuda_only.ps1`
- Move: `scripts/package_cuda_release.ps1` -> `scripts/ops/package_cuda_release.ps1`
- Move legacy CPU/OpenSplat prototype scripts to `scripts/legacy/`
- Modify: `README-CUDA.md`
- Modify: `docs/cuda-migration.md`

- [ ] **Step 1: Create script directories**

Create `scripts/ops/`, `scripts/dev/`, and `scripts/legacy/`.

- [ ] **Step 2: Move CUDA operational scripts**

Place actively supported CUDA scripts in `scripts/ops/`.

- [ ] **Step 3: Move CPU-era scripts to legacy**

Place CPU/OpenSplat smoke-test scripts in `scripts/legacy/` with a README warning that CUDA-only is the supported path.

- [ ] **Step 4: Update docs**

Update all script paths in README and CUDA migration docs.

### Task 5: Docker Layout

**Files:**
- Keep: `docker/opensplat-cuda.Dockerfile`
- Move: `docker/opensplat-cpu.Dockerfile` -> `docker/legacy/opensplat-cpu.Dockerfile`
- Create: `docker/README.md`

- [ ] **Step 1: Move CPU Dockerfile to legacy**

CPU Dockerfile is retained only as historical reference, not active workflow.

- [ ] **Step 2: Document CUDA-only Docker usage**

`docker/README.md` points to CUDA image build and future Nerfstudio/Splatfacto image work.

### Task 6: Verification and Commit

**Files:**
- All moved files

- [ ] **Step 1: Run full test suite**

Run: `$env:PYTHONPATH='D:\.codex_workplace\3DGS\apps\api'; python -m pytest apps/api/tests`
Expected: all tests pass.

- [ ] **Step 2: Generate package smoke test**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ops\package_cuda_release.ps1 -PackageName refactor-smoke.zip`
Expected: zip generated under `artifacts/`, ignored by git, containing `README-CUDA.md`.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`
Expected: only intentional source/doc moves and edits appear.

- [ ] **Step 4: Commit**

Commit message: `refactor: restructure cuda-only workspace`
