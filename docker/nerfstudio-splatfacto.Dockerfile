FROM nvcr.io/nvidia/cuda:12.8.1-devel-ubuntu24.04

ARG UBUNTU_MIRROR=https://mirrors.aliyun.com/ubuntu
ARG COLMAP_VERSION=3.13.0
ARG COLMAP_REPOSITORY=https://github.com/colmap/colmap.git

ENV DEBIAN_FRONTEND=noninteractive
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
ENV CUDA_VISIBLE_DEVICES=0,1,2,3
ENV HTTP_PROXY="" HTTPS_PROXY="" ALL_PROXY="" FTP_PROXY="" \
    http_proxy="" https_proxy="" all_proxy="" ftp_proxy="" \
    NO_PROXY="localhost,127.0.0.1,::1,mirrors.aliyun.com,developer.download.nvidia.cn,download.pytorch.org,github.com" \
    no_proxy="localhost,127.0.0.1,::1,mirrors.aliyun.com,developer.download.nvidia.cn,download.pytorch.org,github.com"

RUN if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list.d/ubuntu.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list; \
    fi \
    && printf 'Acquire::http::Proxy "false";\nAcquire::https::Proxy "false";\n' > /etc/apt/apt.conf.d/99-no-proxy

RUN env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u FTP_PROXY -u http_proxy -u https_proxy -u all_proxy -u ftp_proxy \
    apt-get update && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u FTP_PROXY -u http_proxy -u https_proxy -u all_proxy -u ftp_proxy \
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
    procps \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u FTP_PROXY -u http_proxy -u https_proxy -u all_proxy -u ftp_proxy \
    git clone --branch "${COLMAP_VERSION}" --depth 1 "${COLMAP_REPOSITORY}" /tmp/colmap \
    && cmake -S /tmp/colmap -B /tmp/colmap/build -GNinja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_ARCHITECTURES=120 \
        -DCUDA_ENABLED=ON \
        -DGUI_ENABLED=OFF \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
    && cmake --build /tmp/colmap/build --target install -j"$(nproc)" \
    && ldconfig \
    && rm -rf /tmp/colmap

ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ARG PIP_TRUSTED_HOST=mirrors.aliyun.com
ENV PIP_NO_CACHE_DIR=1
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=20

RUN python3 -m venv /opt/venv
RUN env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u FTP_PROXY -u http_proxy -u https_proxy -u all_proxy -u ftp_proxy \
    python -m pip install --retries 20 --timeout 300 --upgrade pip setuptools wheel

# CUDA 12.8 wheels are required for RTX 5090 / Blackwell sm_120 support.
RUN env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u FTP_PROXY -u http_proxy -u https_proxy -u all_proxy -u ftp_proxy \
    python -m pip install --retries 20 --timeout 300 --index-url https://download.pytorch.org/whl/cu128 --extra-index-url "${PIP_INDEX_URL}" \
    "torch==2.11.0+cu128" \
    "torchvision==0.26.0+cu128" \
    "torchaudio==2.11.0+cu128"

RUN env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u FTP_PROXY -u http_proxy -u https_proxy -u all_proxy -u ftp_proxy \
    python -m pip install --retries 20 --timeout 300 --prefer-binary \
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
RUN colmap -h 2>&1 | tee /tmp/colmap-help.txt && ! grep -qi "without CUDA" /tmp/colmap-help.txt
RUN ns-train splatfacto --help >/tmp/ns-train-splatfacto-help.txt
RUN ns-export gaussian-splat --help >/tmp/ns-export-gaussian-splat-help.txt
RUN ns-process-data images --help >/tmp/ns-process-data-images-help.txt
RUN python -c "import fastapi, uvicorn, httpx, multipart"

WORKDIR /workspace
