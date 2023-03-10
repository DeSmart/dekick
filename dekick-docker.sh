#!/usr/bin/env bash

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
# DOCKER_DEFAULT_PLATFORM="linux/amd64"
# if [ "$HOST_ARCH" = "arm64" ]; then
#   DOCKER_DEFAULT_PLATFORM="linux/arm64"
# fi
# export DOCKER_DEFAULT_PLATFORM

VOLUME_DEKICK="-v "${DEKICK_PATH}:${DEKICK_PATH}""
VOLUME_PROJECT="-v "${PROJECT_ROOT}:${PROJECT_ROOT}""

if [ "$DEKICK_PATH" = "$PROJECT_ROOT" ]; then
  VOLUME_PROJECT=""
fi

if [[ "$(docker images -q "${IMAGE}" 2> /dev/null)" == "" ]]; then
  echo -n "Downloading DeKick image... "
  docker pull -q "${IMAGE}"
fi

CURRENT_UID=$(id -u)
CURRENT_USERNAME=$(whoami)

if [ "$CURRENT_UID" = "0" ]; then
  CURRENT_UID=1000
  CURRENT_USERNAME="dekick"
fi

docker run $DOCKER_FLAGS --rm \
  ${VOLUME_DEKICK} \
  ${VOLUME_PROJECT} \
  -e DEKICK_PATH="${DEKICK_PATH}" \
  -e PROJECT_ROOT="${PROJECT_ROOT}" \
  -e CURRENT_UID="${CURRENT_UID}" \
  -e CURRENT_USERNAME="${CURRENT_USERNAME}" \
  -e DEKICK_DOCKER_IMAGE="${IMAGE}" \
  -e DEKICK_DEBUGGER="${DEKICK_DEBUGGER}" \
  -e HOST_ARCH="${HOST_ARCH}" \
  -e HOST_PLATFORM="${HOST_PLATFORM}" \
  --add-host proxy:host-gateway \
  ${DEKICK_DOCKER_PORTS} \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.gitlabrc:/tmp/.gitlabrc \
  "${IMAGE}" \
  "$@"

DEKICK_EXIT_CODE=$?

if [ "$DEKICK_EXIT_CODE" = 255 ]; then
  echo
  echo "Restarting DeKick after update from version ${VERSION}"
  "${DEKICK_PATH}/dekick-docker.sh" "$@" --migrate-from-version="${VERSION}"
  exit 0
fi

exit $DEKICK_EXIT_CODE