FROM ubuntu:22.04

ENV TERM=xterm DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    cmake git-core gcc-arm-none-eabi libnewlib-arm-none-eabi build-essential wget python3

WORKDIR /

RUN git clone -b v1.24.1 --depth=1 --recursive https://github.com/micropython/micropython.git

WORKDIR micropython

RUN make -C ports/rp2 submodules && make -C mpy-cross clean

RUN sed -i 's/progsize=256)/progsize=1024)/g' ports/rp2/modules/_boot.py

COPY uf2_build/copy_and_compile.sh /

WORKDIR /

ARG program
ENV main_py=${program}

ENTRYPOINT [ "sh", "copy_and_compile.sh" ]
