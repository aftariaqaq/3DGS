FROM 3dgs-runtime:rtx5090

ARG UBUNTU_MIRROR=https://mirrors.aliyun.com/ubuntu
ARG COLMAP_VERSION=3.13.0
ARG COLMAP_REPOSITORY=https://github.com/colmap/colmap.git

ENV DEBIAN_FRONTEND=noninteractive
ENV HTTP_PROXY="" HTTPS_PROXY="" ALL_PROXY="" FTP_PROXY="" \
    http_proxy="" https_proxy="" all_proxy="" ftp_proxy="" \
    NO_PROXY="localhost,127.0.0.1,::1,mirrors.aliyun.com,developer.download.nvidia.cn,github.com" \
    no_proxy="localhost,127.0.0.1,::1,mirrors.aliyun.com,developer.download.nvidia.cn,github.com"

RUN if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list.d/ubuntu.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" /etc/apt/sources.list; \
    fi \
    && printf 'Acquire::http::Proxy "false";\nAcquire::https::Proxy "false";\n' > /etc/apt/apt.conf.d/99-no-proxy

RUN env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u FTP_PROXY -u http_proxy -u https_proxy -u all_proxy -u ftp_proxy \
    apt-get update && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u FTP_PROXY -u http_proxy -u https_proxy -u all_proxy -u ftp_proxy \
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

RUN colmap -h 2>&1 | tee /tmp/colmap-help.txt && ! grep -qi "without CUDA" /tmp/colmap-help.txt
