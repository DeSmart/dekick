#!/bin/bash

DEKICK_COMMANDS=("artisan" "build" "composer" "docker-compose" "knex" "local" "logs" "node" "npm" "npx" "phpunit" "pint" "seed" "status" "stop" "test" "update" "yarn")

ln -s "${DEKICK_PATH}/dekick.py" /usr/bin/dekick

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
