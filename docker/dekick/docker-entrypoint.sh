#!/bin/bash

user=$(whoami)

ln -s "${DEKICK_PATH}/dekick.py" /usr/bin/dekick > /dev/null 2>&1

if [ "$user" = "root" ] && [ -n "$CURRENT_USERNAME" ] && [ -n "$CURRENT_UID" ]; then
  adduser -D -h /tmp/homedir -u "${CURRENT_UID}" "${CURRENT_USERNAME}"
  chmod oug+rwX /var/run/docker.sock
  echo "${CURRENT_USERNAME} ALL=(ALL) NOPASSWD:/bin/rm" >> /etc/sudoers
  su -p -c "/usr/local/bin/docker-entrypoint.sh $*" "${CURRENT_USERNAME}"
  exit $?
fi

# shellcheck disable=SC1091
source "$DEKICK_PATH/commands.sh"

export HOME=/tmp/homedir

if [ -z "$1" ]; then
    dekick -h
    exit 1
fi

if [[ " ${DEKICK_COMMANDS[*]} " == *" $1 "* ]]; then
  cd "${PROJECT_ROOT}" || cd /
  dekick "$@"
elif command -v "$1" > /dev/null 2>&1; then
  cd "${DEKICK_PATH}" || cd /
  exec "$@"
else
  dekick --help
fi