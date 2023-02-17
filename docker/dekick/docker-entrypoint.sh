#!/bin/bash

DEKICK_COMMANDS=("artisan" "build" "composer" "docker-compose" "knex" "local" "logs" "node" "npm" "npx" "phpunit" "pint" "seed" "status" "stop" "test" "update" "yarn")

user=$(whoami)

if [ "$user" = "root" ] && [ -n "$CURRENT_USERNAME" ]; then
  user=${CURRENT_UID}
  ln -s "${DEKICK_PATH}/dekick.py" /usr/bin/dekick
  adduser -D -h /tmp/homedir -u "${user}" "$CURRENT_USERNAME"
  chown "${user}" /var/run/docker.sock
  echo "${CURRENT_USERNAME} ALL=(ALL) NOPASSWD:/bin/rm" >> /etc/sudoers
  su -c "/usr/local/bin/docker-entrypoint.sh $*" "$CURRENT_USERNAME"
  exit $?
fi

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