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
node_mode="${SUPERSPLAT_NODE_MODE:-auto}"
default_npm_registries="https://registry.npmmirror.com https://mirrors.cloud.tencent.com/npm/ https://mirrors.huaweicloud.com/repository/npm/ https://registry.npmjs.org"
npm_registries="${SUPERSPLAT_NPM_REGISTRIES:-${SUPERSPLAT_NPM_REGISTRY:-${default_npm_registries}}}"
nvm_root="${SUPERSPLAT_NVM_ROOT:-/root/.nvm}"
npm_cache="${SUPERSPLAT_NPM_CACHE:-/root/.npm}"
scene_dir="${repo_root}/data/scenes/${scene_id}"
export_dir="${repo_root}/data/jobs/${job_id}/nerfstudio/exports"
source_ply="${export_dir}/splat.ply"
host_node_bin="${SUPERSPLAT_NODE_BIN:-$(command -v node || true)}"
host_npm_bin="${SUPERSPLAT_NPM_BIN:-$(command -v npm || true)}"
host_node_prefix=""

if [ -n "${host_node_bin}" ]; then
  host_node_prefix="$(cd "$(dirname "${host_node_bin}")/.." && pwd)"
fi

if [ ! -f "${source_ply}" ]; then
  source_ply="$(find "${export_dir}" -maxdepth 1 -type f -name '*.ply' | sort | head -n 1 || true)"
fi

if [ -z "${source_ply}" ] || [ ! -f "${source_ply}" ]; then
  echo "Splatfacto PLY output not found under ${export_dir}" >&2
  exit 1
fi

mkdir -p "${scene_dir}"
cp -f "${source_ply}" "${scene_dir}/source.ply"

run_splat_transform_host() {
  local registry="$1"
  shift

  (
    cd "${repo_root}"
    npm_config_registry="${registry}" npm exec --yes @playcanvas/splat-transform@2.4.0 -- "$@"
  )
}

run_splat_transform_runtime_nvm() {
  local registry="$1"
  shift

  mkdir -p "${npm_cache}"

  docker run --rm \
    -e PATH="${host_node_prefix}/bin:/opt/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    -e npm_config_registry="${registry}" \
    -v "${repo_root}:/workspace" \
    -v "${nvm_root}:${nvm_root}:ro" \
    -v "${npm_cache}:${npm_cache}" \
    -w /workspace \
    3dgs-runtime:rtx5090 \
    npm exec --yes @playcanvas/splat-transform@2.4.0 -- "$@"
}

run_splat_transform_docker() {
  local registry="$1"
  shift

  docker run --rm \
    -v "${repo_root}:/workspace" \
    -e npm_config_registry="${registry}" \
    -w /workspace \
    "${node_image}" \
    npm exec --yes @playcanvas/splat-transform@2.4.0 -- "$@"
}

has_host_npm() {
  [ -n "${host_npm_bin}" ] && [ -x "${host_npm_bin}" ]
}

has_runtime_nvm() {
  has_host_npm && [ -n "${host_node_prefix}" ] && [ -d "${nvm_root}" ]
}

run_conversion_pair() {
  local runner="$1"
  local source_path="$2"
  local sog_path="$3"
  local html_path="$4"
  local registry

  for registry in ${npm_registries}; do
    echo "Trying npm registry ${registry}"
    rm -f "${scene_dir}/scene.sog" "${scene_dir}/supersplat.html"

    if "${runner}" "${registry}" \
      -w "${source_path}" \
      --filter-nan \
      -r 180,0,0 \
      "${sog_path}" && \
      "${runner}" "${registry}" \
      -w "${source_path}" \
      --filter-nan \
      -r 180,0,0 \
      "${html_path}"; then
      echo "SuperSplat conversion succeeded with npm registry ${registry}"
      return 0
    fi

    echo "SuperSplat conversion failed with npm registry ${registry}; trying next candidate" >&2
  done

  echo "SuperSplat conversion failed with all npm registry candidates: ${npm_registries}" >&2
  return 1
}

if [ "${node_mode}" = "runtime-nvm" ] && has_runtime_nvm; then
  echo "Using 3dgs-runtime with mounted host nvm/npm for SuperSplat conversion"
  run_conversion_pair \
    run_splat_transform_runtime_nvm \
    "/workspace/data/scenes/${scene_id}/source.ply" \
    "/workspace/data/scenes/${scene_id}/scene.sog" \
    "/workspace/data/scenes/${scene_id}/supersplat.html"
elif [ "${node_mode}" = "runtime-nvm" ]; then
  echo "SUPERSPLAT_NODE_MODE=runtime-nvm requested, but node/npm or ${nvm_root} was not found" >&2
  exit 1
elif [ "${node_mode}" = "auto" ] && has_runtime_nvm; then
  echo "Using 3dgs-runtime with mounted host nvm/npm for SuperSplat conversion"
  run_conversion_pair \
    run_splat_transform_runtime_nvm \
    "/workspace/data/scenes/${scene_id}/source.ply" \
    "/workspace/data/scenes/${scene_id}/scene.sog" \
    "/workspace/data/scenes/${scene_id}/supersplat.html"
elif { [ "${node_mode}" = "auto" ] || [ "${node_mode}" = "host" ]; } && has_host_npm; then
  echo "Using host npm for SuperSplat conversion"
  run_conversion_pair \
    run_splat_transform_host \
    "${scene_dir}/source.ply" \
    "${scene_dir}/scene.sog" \
    "${scene_dir}/supersplat.html"
elif [ "${node_mode}" = "host" ]; then
  echo "SUPERSPLAT_NODE_MODE=host requested, but npm was not found on PATH" >&2
  exit 1
else
  echo "Using Docker image ${node_image} for SuperSplat conversion"
  run_conversion_pair \
    run_splat_transform_docker \
    "/workspace/data/scenes/${scene_id}/source.ply" \
    "/workspace/data/scenes/${scene_id}/scene.sog" \
    "/workspace/data/scenes/${scene_id}/supersplat.html"
fi

docker run --rm \
  -e PYTHONPATH=/workspace/apps/api \
  -v "${repo_root}:/workspace" \
  -w /workspace \
  3dgs-runtime:rtx5090 \
  python -c "import json; from datetime import datetime, timezone; from pathlib import Path; from app.models import JobStatus; from app.services import job_store; job_id='${job_id}'; scene_id='${scene_id}'; scene_dir=Path('/workspace/data/scenes') / scene_id; model_path=scene_dir / 'scene.sog'; source_path=scene_dir / 'source.ply'; job=job_store.read_job(job_id); stats={'model_size_bytes': model_path.stat().st_size, 'source_model_size_bytes': source_path.stat().st_size}; frame_count=job.get('frame_count') or job.get('max_frames'); stats.update({'frame_count': frame_count} if frame_count is not None else {}); scene={'id': scene_id, 'job_id': job_id, 'name': scene_id, 'model_type': 'sog', 'model_url': f'/static/scenes/{scene_id}/scene.sog', 'source_model_url': f'/static/scenes/{scene_id}/source.ply', 'viewer_url': f'/scenes/{scene_id}/supersplat', 'fallback_viewer_url': f'/scenes/{scene_id}/viewer', 'supersplat_viewer_url': f'/static/scenes/{scene_id}/supersplat.html', 'created_at': datetime.now(timezone.utc).isoformat(), 'stats': stats}; (scene_dir / 'metadata.json').write_text(json.dumps(scene, indent=2), encoding='utf-8'); job_store.update_status(job_id, JobStatus.EXPORTING_MODEL, stage='Converting SuperSplat scene'); job_store.mark_ready(job_id, scene_id, scene['model_url']); print(scene)"
