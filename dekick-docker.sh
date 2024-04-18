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

if [ -n "$WSL_DISTRO_NAME" ]; then
  HOST_SUBSYSTEM="wsl"
else
  HOST_SUBSYSTEM="default"
fi

if ! tty > /dev/null 2>&1; then
  DOCKER_FLAGS=""
fi

DEKICK_DOCKER_PORTS=""
if [ -n "$DBG" ]; then
  DEKICK_DEBUGGER="true"
  export DEKICK_DEBUGGER
fi

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

# When running as root (in CI/CD for example) use dekick user with uid 1000
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

# Add xhost authorization and other things needed for Cypress to run e2e tests or open GUI apps
if [ "$1" = "e2e" ]; then

  X11SOCKET="-v /tmp/.X11-unix:/tmp/.X11-unix"

  # Detect if there's a xhost command available and if not prompt to install XQuartz
  if [ "${HOST_PLATFORM}" = "Darwin" ] && ! command -v xhost > /dev/null 2>&1; then
    echo -e "Please install XQuartz XServer first! https://www.xquartz.org/.\n\nAfter installing, please remember to check 'Allow connections from network clients' in XQuartz settings."
    exit 1
  fi

  if [ "${HOST_PLATFORM}" = "Darwin" ]; then
    for i in {0..9}; do
      HOST_IP=$(ifconfig "en${i}" | grep -w inet | awk '{print $2}')
      if [ -n "$HOST_IP" ]; then
        break
      fi
    done
    xhost + "$HOST_IP" > /dev/null 2>&1
  elif [ "${HOST_PLATFORM}" = "Linux" ]; then
      xhost + > /dev/null 2>&1
  fi

fi

DOCKER_CONTAINER_NAME=""
if [ "$1" == "pytest" ]; then

  function pytest_stop() {
    echo "Stopping PyTest..."
    docker kill pytest > /dev/null 2>&1
    sleep 2
    docker rm -f pytest > /dev/null 2>&1
    sleep 2
    rm -f "${DEKICK_PATH}/tmp/pytest.lock" > /dev/null 2>&1
    if [ -d "${DEKICK_PATH}/tmp/dind_containers" ]; then
      echo "Cleaning up dangling dind containers..."
      for file in "${DEKICK_PATH}"/tmp/dind_containers/*; do
        docker rm -f "$(basename "$file")" > /dev/null 2>&1
        rm -f "$file" > /dev/null 2>&1
      done
    fi
  }

  DOCKER_CONTAINER_NAME="--name pytest"
  if docker ps --filter "name=pytest" --format '{{.Names}}' | grep -q pytest; then
  
    if [[ -t 1 ]]; then
      echo -n "PyTest already running, should I kill it? [y/N] "
      read -r answer
      if [ "$answer" = "${answer#[nN]}" ]; then
        pytest_stop
      else
        echo -e "\nOk, another PyTest is still running, exiting..."
        exit 0
      fi
    else
      pytest_stop
    fi
  fi
fi

docker run $DOCKER_FLAGS --rm \
  ${DOCKER_CONTAINER_NAME} \
  ${VOLUME_DEKICK} \
  ${VOLUME_PROJECT} \
  ${VOLUME_BOILERPLATES} \
  ${DEKICK_DOCKER_PORTS} \
  ${DEKICK_GITLABRC} \
  ${X11SOCKET} \
  -e DEKICK_BOILERPLATES_INSTALL_PATH="${DEKICK_BOILERPLATES_INSTALL_PATH}" \
  -e CURRENT_UID="${CURRENT_UID}" \
  -e CURRENT_USERNAME="${CURRENT_USERNAME}" \
  -e DEKICK_DEBUGGER="${DEKICK_DEBUGGER}" \
  -e DEKICK_DOCKER_IMAGE="${IMAGE}" \
  -e DEKICK_PATH="${DEKICK_PATH}" \
  -e HOST_ARCH="${HOST_ARCH}" \
  -e HOST_HOME="${HOST_HOME}" \
  -e HOST_PLATFORM="${HOST_PLATFORM}" \
  -e WSL_DISTRO_NAME="${WSL_DISTRO_NAME}" \
  -e HOST_SUBSYSTEM="${HOST_SUBSYSTEM}" \
  -e PROJECT_ROOT="${PROJECT_ROOT}" \
  -e DISPLAY="${DISPLAY}" \
  -e HOST_IP="${HOST_IP}" \
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