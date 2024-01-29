FROM docker:25.0.1-dind-alpine3.19

RUN apk update\
  && apk add --no-cache git bash curl ncurses net-tools jq perl gettext rsync python3 py3-pip sudo \
  && rm -rf /var/cache/apk/*

COPY requirements.txt /tmp/requirements.txt
COPY dockerd-entrypoint.sh /usr/local/bin/
COPY base/* /

RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt


ENTRYPOINT ["dockerd-entrypoint.sh"]
CMD []
