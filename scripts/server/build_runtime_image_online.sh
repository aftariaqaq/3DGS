#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-3dgs-runtime:rtx5090}"
TAR_PATH="${TAR_PATH:-/data/3dgs/3dgs-runtime-rtx5090.tar}"
UBUNTU_MIRROR="${UBUNTU_MIRROR:-https://mirrors.aliyun.com/ubuntu}"
PIP_INDEX_URL="${PIP_INDEX_URL:-https://mirrors.aliyun.com/pypi/simple}"
PIP_TRUSTED_HOST="${PIP_TRUSTED_HOST:-mirrors.aliyun.com}"
COLMAP_REPOSITORY="${COLMAP_REPOSITORY:-https://github.com/colmap/colmap.git}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DOCKERFILE="${REPO_ROOT}/docker/nerfstudio-splatfacto.Dockerfile"

unset HTTP_PROXY HTTPS_PROXY ALL_PROXY FTP_PROXY
unset http_proxy https_proxy all_proxy ftp_proxy

mkdir -p "$(dirname "${TAR_PATH}")"

docker build \
  --progress plain \
  --build-arg "UBUNTU_MIRROR=${UBUNTU_MIRROR}" \
  --build-arg "PIP_INDEX_URL=${PIP_INDEX_URL}" \
  --build-arg "PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}" \
  --build-arg "COLMAP_REPOSITORY=${COLMAP_REPOSITORY}" \
  --build-arg "HTTP_PROXY=" \
  --build-arg "HTTPS_PROXY=" \
  --build-arg "ALL_PROXY=" \
  --build-arg "FTP_PROXY=" \
  --build-arg "http_proxy=" \
  --build-arg "https_proxy=" \
  --build-arg "all_proxy=" \
  --build-arg "ftp_proxy=" \
  -f "${DOCKERFILE}" \
  -t "${IMAGE_NAME}" \
  "${REPO_ROOT}"

docker run --rm --network none "${IMAGE_NAME}" bash -lc '
set -e
ns-train splatfacto --help >/tmp/ns-train-offline-help.txt
ns-export gaussian-splat --help >/tmp/ns-export-offline-help.txt
python /opt/3dgs/prewarm_nerfstudio.py
python -c "from tensorboard.backend.event_processing.event_accumulator import EventAccumulator; print(\"tensorboard events ok\")"
colmap -h 2>&1 | tee /tmp/colmap-help.txt
! grep -qi "without CUDA" /tmp/colmap-help.txt
'

rm -f "${TAR_PATH}"
docker save -o "${TAR_PATH}" "${IMAGE_NAME}"
sha256sum "${TAR_PATH}" | tee "${TAR_PATH}.sha256"

echo "Runtime image archive created: ${TAR_PATH}"
echo "Copy ${TAR_PATH} and ${TAR_PATH}.sha256 to the offline GPU server."
