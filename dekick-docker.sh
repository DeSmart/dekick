#!/bin/bash

if [ -z "$DEKICK_PATH" ]; then
  DEKICK_PATH=$(pwd)
fi

PWD=$(pwd)
VERSION=$(cat "${DEKICK_PATH}/.version")
IMAGE="desmart/dekick:${VERSION}"
DOCKER_FLAGS="-it"
HOST_ARCH="$(uname -m)"
HOST_PLATFORM="$(uname -s)"

if ! tty > /dev/null 2>&1; then
  DOCKER_FLAGS=""
fi

DEKICK_DOCKER_PORTS=""
if [ "$DEKICK_DEBUGGER" ]; then
  DEKICK_DOCKER_PORTS="-p 8753:8753"
fi

# Architecture detection (arm64, amd64])
DOCKER_DEFAULT_PLATFORM="linux/amd64"
if [ "$HOST_ARCH" = "arm64" ]; then
  DOCKER_DEFAULT_PLATFORM="linux/arm64"
fi
export DOCKER_DEFAULT_PLATFORM

VOLUME_DEKICK="-v "${DEKICK_PATH}:${DEKICK_PATH}""
VOLUME_PROJECT="-v "${PROJECT_ROOT}:${PROJECT_ROOT}""

if [ "$DEKICK_PATH" = "$PROJECT_ROOT" ]; then
  VOLUME_PROJECT=""
fi

docker run $DOCKER_FLAGS --rm \
  ${VOLUME_DEKICK} \
  ${VOLUME_PROJECT} \
  -e DEKICK_PATH="${DEKICK_PATH}" \
  -e PROJECT_ROOT="${PROJECT_ROOT}" \
  -e CURRENT_UID="$(id -u):$(id -g)" \
  -e DEKICK_DOCKER_IMAGE="${IMAGE}" \
  -e DEKICK_DEBUGGER="${DEKICK_DEBUGGER}" \
  -e HOST_ARCH="${HOST_ARCH}" \
  -e HOST_PLATFORM="${HOST_PLATFORM}" \
  -e PYTHONDONTWRITEBYTECODE=1 \
  ${DEKICK_DOCKER_PORTS} \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.gitlabrc:/root/.gitlabrc \
  "${IMAGE}" \
  "$@"

if [ "$?" = 127 ]; then
  echo
  echo "Restarting DeKick after update from version ${VERSION}"
  "${DEKICK_PATH}/dekick-docker.sh" "$@" --migrate-from-version="${VERSION}"
  exit 0
fi