FROM docker:27.3.1-dind-alpine3.20

RUN apk update\
  && apk add --no-cache git bash curl ncurses net-tools jq perl gettext rsync python3 py3-pip sudo grep \
  && rm -rf /var/cache/apk/*

COPY requirements.txt /tmp/requirements.txt
COPY dockerd-entrypoint.sh /usr/local/bin/
COPY base/* /

RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt && rm /tmp/requirements.txt; python -m compileall


ENTRYPOINT ["dockerd-entrypoint.sh"]
CMD []
