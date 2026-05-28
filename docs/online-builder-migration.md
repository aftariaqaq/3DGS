# Online Builder Migration Package

Use this package on a server that can download from Docker, Ubuntu mirrors, PyPI mirrors, PyTorch wheels, GitHub, and NVIDIA CUDA package sources. The output is the offline Docker archive used by the GPU server.

## What This Package Contains

- Project source code.
- Dockerfiles.
- Server run scripts.
- Runtime validation scripts.
- Android capture app source.
- Tests and docs.

It intentionally does not include:

- `artifacts/`
- `data/`
- `test_video/`
- Docker image tar files.
- Android build outputs.

## Build On The Online Server

Unpack under `/data/3dgs/repo`:

```bash
mkdir -p /data/3dgs
tar -xzf 3dgs-online-builder-source-*.tar.gz -C /data/3dgs
mv /data/3dgs/3DGS /data/3dgs/repo
cd /data/3dgs/repo
```

Build and save the offline runtime image:

```bash
bash scripts/server/build_runtime_image_online.sh
```

Default output:

```text
/data/3dgs/3dgs-runtime-rtx5090.tar
/data/3dgs/3dgs-runtime-rtx5090.tar.sha256
```

The script uses mirror defaults and clears proxy environment variables before mirror downloads:

```text
UBUNTU_MIRROR=https://mirrors.aliyun.com/ubuntu
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
PIP_TRUSTED_HOST=mirrors.aliyun.com
```

Override them only if the online server has a faster local mirror:

```bash
UBUNTU_MIRROR=https://your-ubuntu-mirror.example/ubuntu \
PIP_INDEX_URL=https://your-pypi-mirror.example/simple \
PIP_TRUSTED_HOST=your-pypi-mirror.example \
bash scripts/server/build_runtime_image_online.sh
```

## Move To Offline GPU Server

Copy the generated files to the target offline server:

```text
/data/3dgs/3dgs-runtime-rtx5090.tar
/data/3dgs/3dgs-runtime-rtx5090.tar.sha256
```

Then on the offline server:

```bash
cd /data/3dgs
sha256sum -c 3dgs-runtime-rtx5090.tar.sha256
docker load -i 3dgs-runtime-rtx5090.tar
```

After loading, use `docs/offline-rtx5090-runbook.md` for API, training, metrics, COLMAP monitoring, and viewer validation.
