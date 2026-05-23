FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG OPENSPLAT_REPO=https://github.com/pierotofy/OpenSplat.git
ARG OPENSPLAT_REF=main
ARG CUDA_VERSION=12.1.1
ARG TORCH_VERSION=2.2.1
ARG CMAKE_CUDA_ARCHITECTURES=75;80;86;89
ARG CMAKE_BUILD_TYPE=Release

SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      cmake \
      git \
      libopencv-dev \
      ninja-build \
      sudo \
      unzip \
      wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "${OPENSPLAT_REF}" "${OPENSPLAT_REPO}" OpenSplat

WORKDIR /opt/OpenSplat

RUN bash .github/workflows/cuda/Linux.sh "ubuntu-22.04" "${CUDA_VERSION}"

RUN wget --no-check-certificate -nv \
      "https://download.pytorch.org/libtorch/cu${CUDA_VERSION%%.*}$(echo ${CUDA_VERSION} | cut -d'.' -f2)/libtorch-cxx11-abi-shared-with-deps-${TORCH_VERSION}%2Bcu${CUDA_VERSION%%.*}$(echo ${CUDA_VERSION} | cut -d'.' -f2).zip" \
      -O libtorch.zip && \
    unzip -q libtorch.zip -d . && \
    rm libtorch.zip

RUN source ".github/workflows/cuda/Linux-env.sh" "cu${CUDA_VERSION%%.*}$(echo ${CUDA_VERSION} | cut -d'.' -f2)" && \
    cmake -S . -B build \
      -GNinja \
      -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE}" \
      -DCMAKE_PREFIX_PATH=/opt/OpenSplat/libtorch \
      -DCMAKE_CUDA_ARCHITECTURES="${CMAKE_CUDA_ARCHITECTURES}" \
      -DCUDA_TOOLKIT_ROOT_DIR="${CUDA_HOME}" \
      -DGPU_RUNTIME=CUDA && \
    cmake --build build --config "${CMAKE_BUILD_TYPE}"

ENV LD_LIBRARY_PATH=/opt/OpenSplat/libtorch/lib

ENTRYPOINT ["/opt/OpenSplat/build/opensplat"]
