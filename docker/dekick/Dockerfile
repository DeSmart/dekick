FROM docker:23.0.1-cli-alpine3.17

RUN apk update\
  && apk add --no-cache git bash curl ncurses net-tools jq perl gettext rsync python3 py3-pip sudo \
  && rm -rf /var/cache/apk/*

COPY requirements.txt /tmp/requirements.txt
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

ENTRYPOINT [ "docker-entrypoint.sh" ]