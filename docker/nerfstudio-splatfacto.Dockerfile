FROM nvcr.io/nvidia/cuda:12.8.1-devel-ubuntu24.04

ARG UBUNTU_MIRROR=https://mirrors.aliyun.com/ubuntu
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}
ENV PIP_DEFAULT_TIMEOUT=120
ENV PIP_RETRIES=10
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
ENV CUDA_VISIBLE_DEVICES=0,1,2,3

RUN if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list.d/ubuntu.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list; \
    fi

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
RUN python -m pip install --index-url https://download.pytorch.org/whl/cu128 --extra-index-url "${PIP_INDEX_URL}" \
    "torch==2.11.0+cu128" \
    "torchvision==0.26.0+cu128" \
    "torchaudio==2.11.0+cu128"

RUN python -m pip install --prefer-binary \
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
