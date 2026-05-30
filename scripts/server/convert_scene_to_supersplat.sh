#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <job_id> [scene_id]" >&2
  exit 2
fi

job_id="$1"
scene_id="${2:-scene_${job_id}}"

docker run --rm \
  -e PYTHONPATH=/workspace/apps/api \
  -e SPLAT_TRANSFORM_COMMAND="${SPLAT_TRANSFORM_COMMAND:-npx --yes @playcanvas/splat-transform@2.4.0}" \
  -v /data/3dgs/repo:/workspace \
  -w /workspace \
  3dgs-runtime:rtx5090 \
  python -c "from app.models import JobStatus; from app.services import job_store, model_exporter; job_id='${job_id}'; scene_id='${scene_id}'; job=job_store.read_job(job_id); job_store.update_status(job_id, JobStatus.EXPORTING_MODEL, stage='Converting SuperSplat scene'); scene=model_exporter.export_scene(job_id, scene_id=scene_id, frame_count=job.get('frame_count') or job.get('max_frames')); job_store.mark_ready(job_id, scene['id'], scene['model_url']); print(scene)"
