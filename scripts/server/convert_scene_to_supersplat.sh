#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <job_id> [scene_id]" >&2
  exit 2
fi

job_id="$1"
scene_id="${2:-scene_${job_id}}"
repo_root="${REPO_ROOT:-/data/3dgs/repo}"
node_image="${SUPERSPLAT_NODE_IMAGE:-node:22-bookworm}"
scene_dir="${repo_root}/data/scenes/${scene_id}"
export_dir="${repo_root}/data/jobs/${job_id}/nerfstudio/exports"
source_ply="${export_dir}/splat.ply"

if [ ! -f "${source_ply}" ]; then
  source_ply="$(find "${export_dir}" -maxdepth 1 -type f -name '*.ply' | sort | head -n 1 || true)"
fi

if [ -z "${source_ply}" ] || [ ! -f "${source_ply}" ]; then
  echo "Splatfacto PLY output not found under ${export_dir}" >&2
  exit 1
fi

mkdir -p "${scene_dir}"
cp -f "${source_ply}" "${scene_dir}/source.ply"

docker run --rm \
  -v "${repo_root}:/workspace" \
  -w /workspace \
  "${node_image}" \
  bash -lc "set -euo pipefail
    npm exec --yes @playcanvas/splat-transform@2.4.0 -- \
      -w /workspace/data/scenes/${scene_id}/source.ply \
      --filter-nan \
      -r 180,0,0 \
      /workspace/data/scenes/${scene_id}/scene.sog
    npm exec --yes @playcanvas/splat-transform@2.4.0 -- \
      -w /workspace/data/scenes/${scene_id}/source.ply \
      --filter-nan \
      -r 180,0,0 \
      /workspace/data/scenes/${scene_id}/supersplat.html
  "

docker run --rm \
  -e PYTHONPATH=/workspace/apps/api \
  -v "${repo_root}:/workspace" \
  -w /workspace \
  3dgs-runtime:rtx5090 \
  python -c "import json; from datetime import datetime, timezone; from pathlib import Path; from app.models import JobStatus; from app.services import job_store; job_id='${job_id}'; scene_id='${scene_id}'; scene_dir=Path('/workspace/data/scenes') / scene_id; model_path=scene_dir / 'scene.sog'; source_path=scene_dir / 'source.ply'; job=job_store.read_job(job_id); stats={'model_size_bytes': model_path.stat().st_size, 'source_model_size_bytes': source_path.stat().st_size}; frame_count=job.get('frame_count') or job.get('max_frames'); stats.update({'frame_count': frame_count} if frame_count is not None else {}); scene={'id': scene_id, 'job_id': job_id, 'name': scene_id, 'model_type': 'sog', 'model_url': f'/static/scenes/{scene_id}/scene.sog', 'source_model_url': f'/static/scenes/{scene_id}/source.ply', 'viewer_url': f'/scenes/{scene_id}/supersplat', 'fallback_viewer_url': f'/scenes/{scene_id}/viewer', 'supersplat_viewer_url': f'/static/scenes/{scene_id}/supersplat.html', 'created_at': datetime.now(timezone.utc).isoformat(), 'stats': stats}; (scene_dir / 'metadata.json').write_text(json.dumps(scene, indent=2), encoding='utf-8'); job_store.update_status(job_id, JobStatus.EXPORTING_MODEL, stage='Converting SuperSplat scene'); job_store.mark_ready(job_id, scene_id, scene['model_url']); print(scene)"
