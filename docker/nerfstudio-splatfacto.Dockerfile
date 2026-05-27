FROM nvcr.io/nvidia/cuda:12.8.1-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
ENV CUDA_VISIBLE_DEVICES=0,1,2,3

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    colmap \
    coreutils \
    findutils \
    git \
    ffmpeg \
    procps \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
RUN python -m pip install --upgrade pip setuptools wheel

# CUDA 12.8 wheels are required for RTX 5090 / Blackwell sm_120 support.
RUN python -m pip install --index-url https://download.pytorch.org/whl/cu128 \
    torch torchvision torchaudio

RUN python -m pip install \
    nerfstudio \
    fastapi \
    "uvicorn[standard]" \
    httpx \
    python-multipart \
    pytest

RUN python --version
RUN python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
RUN ffmpeg -version >/tmp/ffmpeg-version.txt
RUN ffprobe -version >/tmp/ffprobe-version.txt
RUN colmap -h >/tmp/colmap-help.txt
RUN ns-train splatfacto --help >/tmp/ns-train-splatfacto-help.txt
RUN ns-export gaussian-splat --help >/tmp/ns-export-gaussian-splat-help.txt
RUN ns-process-data images --help >/tmp/ns-process-data-images-help.txt
RUN python -c "import fastapi, uvicorn, httpx, multipart"

WORKDIR /workspace
