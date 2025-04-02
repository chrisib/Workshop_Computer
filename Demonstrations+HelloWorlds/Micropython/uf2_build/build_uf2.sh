#!/bin/sh
set -e

# Run this script from the repo's Micropython directory as `bash ./uf2_build/build_uf2.sh`.
# requires docker is installed and running. For docker help: https://docs.docker.com/get-started/

# Build the `workshop_buildenv`` docker image. Subsequent builds will reuse the same image.
docker build -t workshop_buildenv -f uf2_build/Dockerfile ./

# Run the just built docker image, which uses the code in the current directory to build a new uf2
# image, which will be located in `uf2_build/workshop.uf2`.

for py in $(ls programs|grep -e "py$");
do
    docker run -v .:/workshop workshop_buildenv $py
done
