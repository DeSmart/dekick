#!/bin/bash

BASEIMAGE="desmart/dekick"
TAG=$(cat ../.version)
IMAGE="${BASEIMAGE}:${TAG}"

cp ../requirements.txt .
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx create --use --name multiarch
docker buildx inspect --bootstrap
docker buildx build --pull --platform="linux/amd64,linux/arm64/v8" --tag "${IMAGE}" --push .
rm requirements.txt