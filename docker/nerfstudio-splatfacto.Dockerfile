FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    python3 \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip setuptools wheel

# Keep PyTorch and Nerfstudio installation explicit so GPU-host owners can
# adjust versions for new Blackwell/RTX 50-series driver requirements.
RUN python3 -m pip install --index-url https://download.pytorch.org/whl/cu124 \
    torch torchvision torchaudio

RUN python3 -m pip install nerfstudio

RUN ns-train splatfacto --help >/tmp/ns-train-splatfacto-help.txt
RUN ns-export gaussian-splat --help >/tmp/ns-export-gaussian-splat-help.txt
RUN ns-process-data images --help >/tmp/ns-process-data-images-help.txt

WORKDIR /workspace
