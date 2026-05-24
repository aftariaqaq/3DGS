FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG OPENSPLAT_REPO=https://github.com/pierotofy/OpenSplat.git
ARG OPENSPLAT_REF=main
ARG TORCH_VERSION=2.3.1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      cmake \
      git \
      libopencv-dev \
      ninja-build \
      unzip \
      wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "${OPENSPLAT_REF}" "${OPENSPLAT_REPO}" OpenSplat

WORKDIR /opt/OpenSplat

RUN wget --no-check-certificate -nv \
      "https://download.pytorch.org/libtorch/cpu/libtorch-cxx11-abi-shared-with-deps-${TORCH_VERSION}%2Bcpu.zip" \
      -O libtorch.zip && \
    unzip -q libtorch.zip -d . && \
    rm libtorch.zip

RUN cmake -S . -B build \
      -GNinja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_PREFIX_PATH=/opt/OpenSplat/libtorch \
      -DGPU_RUNTIME=CPU && \
    cmake --build build --config Release

ENV LD_LIBRARY_PATH=/opt/OpenSplat/libtorch/lib

ENTRYPOINT ["/opt/OpenSplat/build/opensplat"]
