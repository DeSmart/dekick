#!/bin/bash

DEKICK_COMMANDS=("artisan" "build" "composer" "docker-compose" "knex" "local" "logs" "node" "npm" "npx" "phpunit" "pint" "seed" "status" "stop" "test" "update" "yarn")

user=$(whoami)

if [ "$user" = "root" ]; then
  ln -s "${DEKICK_PATH}/dekick.py" /usr/bin/dekick
  adduser -D -h /tmp/homedir -u "${CURRENT_UID%:*}" "$CURRENT_USERNAME"
  chown "${CURRENT_UID%:*}" /var/run/docker.sock
  su -m "$CURRENT_USERNAME" -c "./docker-entrypoint.sh $@"
fi

if [ -z "$1" ]; then
    dekick -h
    exit 1
fi

if [[ " ${DEKICK_COMMANDS[*]} " == *" $1 "* ]]; then
  cd "${PROJECT_ROOT}" || cd /
  su -m dooshek -c dekick "$@"
elif command -v "$1" > /dev/null 2>&1; then
  cd "${DEKICK_PATH}" || cd /
  su -m dooshek -c "$@"
else
  su -m "$CURRENT_USERNAME" -c "dekick --help"
fi
