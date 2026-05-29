FROM 3dgs-runtime:rtx5090

ARG UBUNTU_MIRROR=http://mirrors.aliyun.com/ubuntu
ARG PIP_INDEX_URL=http://mirrors.aliyun.com/pypi/simple
ARG PIP_TRUSTED_HOST=mirrors.aliyun.com mirror.nju.edu.cn mirror.sjtu.edu.cn pypi.org files.pythonhosted.org github.com release-assets.githubusercontent.com
ARG COLMAP_VERSION=3.13.0
ARG COLMAP_REPOSITORY=https://github.com/colmap/colmap.git

ENV DEBIAN_FRONTEND=noninteractive
ENV XDG_CACHE_HOME=/opt/3dgs-cache
ENV TORCH_HOME=/opt/3dgs-cache/torch
ENV HF_HOME=/opt/3dgs-cache/huggingface
ENV NERFSTUDIO_CACHE_DIR=/opt/3dgs-cache/nerfstudio
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=20
ENV NO_PROXY="localhost,127.0.0.1,::1"
ENV no_proxy="localhost,127.0.0.1,::1"

RUN if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list.d/ubuntu.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list; \
    fi

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cmake \
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
    && rm -rf /var/lib/apt/lists/*

RUN git config --global http.sslVerify false && \
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

RUN colmap -h 2>&1 | tee /tmp/colmap-help.txt && ! grep -qi "without CUDA" /tmp/colmap-help.txt

RUN python -m pip install --retries 20 --timeout 300 \
    --trusted-host mirrors.aliyun.com \
    --trusted-host mirror.nju.edu.cn \
    --trusted-host mirror.sjtu.edu.cn \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host github.com \
    --trusted-host release-assets.githubusercontent.com \
    --prefer-binary tensorboard
COPY scripts/runtime/prewarm_nerfstudio.py /opt/3dgs/prewarm_nerfstudio.py
RUN python /opt/3dgs/prewarm_nerfstudio.py
RUN test -f /opt/3dgs-cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth
RUN rm -f /root/.gitconfig
RUN python -c "from tensorboard.backend.event_processing.event_accumulator import EventAccumulator"
