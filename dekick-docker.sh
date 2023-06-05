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
HOST_DOCKER_SOCK="/var/run/docker.sock"
HOST_HOME=$HOME

if ! tty > /dev/null 2>&1; then
  DOCKER_FLAGS=""
fi

DEKICK_DOCKER_PORTS=""
if [ "$DEKICK_DEBUGGER" ]; then
  DEKICK_DOCKER_PORTS="-p 8753:8753"
fi

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

DEKICK_GLOBAL_PATH="${HOST_HOME}/.config/dekick"
DEKICK_GLOBAL_FILE="${DEKICK_GLOBAL_PATH}/global.yml"

# Create global config file if it doesn't exist
if [ ! -f "${DEKICK_GLOBAL_FILE}" ]; then
  mkdir -p "${DEKICK_GLOBAL_PATH}"
  cp "${DEKICK_PATH}/global_tmpl.yml" "${DEKICK_GLOBAL_FILE}"
fi

# Compatibility with version < 2.3.0
if [ -f "$HOST_HOME/.gitlabrc" ]; then
  DEKICK_GITLABRC="-v $HOST_HOME/.gitlabrc:/tmp/homedir/.gitlabrc"
fi

# Boilerplate install - bind mount current directory
if [ "$1" = "boilerplates" ] && [ "$2" = "install" ]; then
  cd - >/dev/null 2>&1 || exit 1
  DEKICK_BOILERPLATES_INSTALL_PATH=$(readlink -f "$PWD")
  cd - >/dev/null 2>&1 || exit 1
  VOLUME_BOILERPLATES="-v "${DEKICK_BOILERPLATES_INSTALL_PATH}:${DEKICK_BOILERPLATES_INSTALL_PATH}""
fi

docker run $DOCKER_FLAGS --rm \
  ${VOLUME_DEKICK} \
  ${VOLUME_PROJECT} \
  ${VOLUME_BOILERPLATES} \
  ${DEKICK_DOCKER_PORTS} \
  ${DEKICK_GITLABRC} \
  -e DEKICK_BOILERPLATES_INSTALL_PATH="${DEKICK_BOILERPLATES_INSTALL_PATH}" \
  -e CURRENT_UID="${CURRENT_UID}" \
  -e CURRENT_USERNAME="${CURRENT_USERNAME}" \
  -e DEKICK_DEBUGGER="${DEKICK_DEBUGGER}" \
  -e DEKICK_DOCKER_IMAGE="${IMAGE}" \
  -e DEKICK_PATH="${DEKICK_PATH}" \
  -e HOST_ARCH="${HOST_ARCH}" \
  -e HOST_HOME="${HOST_HOME}" \
  -e HOST_PLATFORM="${HOST_PLATFORM}" \
  -e PROJECT_ROOT="${PROJECT_ROOT}" \
  --add-host proxy:host-gateway \
  -v "$HOST_DOCKER_SOCK:/var/run/docker.sock" \
  -v "${DEKICK_GLOBAL_FILE}:/tmp/homedir/.config/dekick/global.yml" \
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