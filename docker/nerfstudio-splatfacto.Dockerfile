FROM nvcr.io/nvidia/cuda:12.8.1-devel-ubuntu24.04

ARG UBUNTU_MIRROR=http://mirrors.aliyun.com/ubuntu
ARG COLMAP_VERSION=3.13.0
ARG COLMAP_REPOSITORY=https://github.com/colmap/colmap.git
ARG PIP_INDEX_URL=http://mirrors.aliyun.com/pypi/simple
ARG PIP_TRUSTED_HOST=mirrors.aliyun.com mirror.nju.edu.cn mirror.sjtu.edu.cn download.pytorch.org pypi.org files.pythonhosted.org github.com release-assets.githubusercontent.com
ARG TORCH_INDEX_URL=http://mirror.nju.edu.cn/pytorch/whl/cu128

ENV DEBIAN_FRONTEND=noninteractive
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
ENV CUDA_VISIBLE_DEVICES=0,1,2,3
ENV XDG_CACHE_HOME=/opt/3dgs-cache
ENV TORCH_HOME=/opt/3dgs-cache/torch
ENV HF_HOME=/opt/3dgs-cache/huggingface
ENV NERFSTUDIO_CACHE_DIR=/opt/3dgs-cache/nerfstudio
ENV PIP_NO_CACHE_DIR=1
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=20
ENV PYTHONHTTPSVERIFY=0
ENV CURL_CA_BUNDLE=""
ENV REQUESTS_CA_BUNDLE=""
ENV SSL_CERT_FILE=""
ENV NO_PROXY="localhost,127.0.0.1,::1"
ENV no_proxy="localhost,127.0.0.1,::1"

RUN printf '%s\n' \
    '[global]' \
    'trusted-host = mirrors.aliyun.com' \
    '               mirror.nju.edu.cn' \
    '               mirror.sjtu.edu.cn' \
    '               download.pytorch.org' \
    '               pypi.org' \
    '               files.pythonhosted.org' \
    '               github.com' \
    '               release-assets.githubusercontent.com' \
    'index-url = http://mirrors.aliyun.com/pypi/simple' \
    'timeout = 300' \
    'retries = 20' \
    > /etc/pip.conf

RUN if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list.d/ubuntu.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list; \
    fi

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    cmake \
    coreutils \
    findutils \
    git \
    ffmpeg \
    libcgal-dev \
    libboost-graph-dev \
    libboost-program-options-dev \
    libboost-system-dev \
    libceres-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libglew-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libmetis-dev \
    libsqlite3-dev \
    ninja-build \
    nodejs \
    npm \
    procps \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global http.sslVerify false && \
    git clone --branch "${COLMAP_VERSION}" --depth 1 "${COLMAP_REPOSITORY}" /tmp/colmap && \
    cmake -S /tmp/colmap -B /tmp/colmap/build -GNinja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_ARCHITECTURES=120 \
        -DCUDA_ENABLED=ON \
        -DGUI_ENABLED=OFF \
        -DCMAKE_INSTALL_PREFIX=/usr/local && \
    cmake --build /tmp/colmap/build --target install -j"$(nproc)" && \
    ldconfig && \
    rm -rf /tmp/colmap

RUN python3 -m venv /opt/venv

RUN python -m pip install --retries 20 --timeout 300 \
    --trusted-host mirrors.aliyun.com \
    --trusted-host mirror.nju.edu.cn \
    --trusted-host mirror.sjtu.edu.cn \
    --trusted-host download.pytorch.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host github.com \
    --trusted-host release-assets.githubusercontent.com \
    --upgrade pip setuptools wheel

# CUDA 12.8 wheels are required for RTX 5090 / Blackwell sm_120 support.
RUN python -m pip install --retries 20 --timeout 300 \
    --trusted-host mirrors.aliyun.com \
    --trusted-host mirror.nju.edu.cn \
    --trusted-host mirror.sjtu.edu.cn \
    --trusted-host download.pytorch.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --index-url "${TORCH_INDEX_URL}" \
    --extra-index-url "${PIP_INDEX_URL}" \
    "torch==2.11.0+cu128" \
    "torchvision==0.26.0+cu128" \
    "torchaudio==2.11.0+cu128"

RUN python -m pip install --retries 20 --timeout 300 \
    --trusted-host mirrors.aliyun.com \
    --trusted-host mirror.nju.edu.cn \
    --trusted-host mirror.sjtu.edu.cn \
    --trusted-host download.pytorch.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host github.com \
    --trusted-host release-assets.githubusercontent.com \
    --prefer-binary \
    nerfstudio \
    tensorboard \
    fastapi \
    "uvicorn[standard]" \
    httpx \
    python-multipart \
    pytest

RUN python --version
RUN python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
RUN ffmpeg -version >/tmp/ffmpeg-version.txt
RUN ffprobe -version >/tmp/ffprobe-version.txt
RUN colmap -h 2>&1 | tee /tmp/colmap-help.txt && ! grep -qi "without CUDA" /tmp/colmap-help.txt
RUN ns-train splatfacto --help >/tmp/ns-train-splatfacto-help.txt
RUN ns-export gaussian-splat --help >/tmp/ns-export-gaussian-splat-help.txt
RUN ns-process-data images --help >/tmp/ns-process-data-images-help.txt
COPY scripts/runtime/prewarm_nerfstudio.py /opt/3dgs/prewarm_nerfstudio.py
RUN python /opt/3dgs/prewarm_nerfstudio.py
RUN test -f /opt/3dgs-cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth

RUN rm -f /root/.gitconfig /etc/pip.conf
ENV PYTHONHTTPSVERIFY=
ENV CURL_CA_BUNDLE=
ENV REQUESTS_CA_BUNDLE=
ENV SSL_CERT_FILE=

RUN python -c "import fastapi, uvicorn, httpx, multipart; from tensorboard.backend.event_processing.event_accumulator import EventAccumulator"

WORKDIR /workspace
