FROM python:3.7-alpine

RUN apk add --update --no-cache --virtual .build-deps gcc musl-dev git && \
    mkdir /app && \
    git clone https://gitlab+deploy-token-163:np4NqeyahGv2Nzo-LA3L@git.rwth-aachen.de/mpolitze/thingsboard-homematic-client.git /app && \
    pip install -r /app/requirements.txt > /dev/null && \
    ln -s /config/config.ini /app/config.ini && \
    apk del .build-deps && \
    printf "*/10 * * * * python /app/src/main.py > /proc/1/fd/1 2> /proc/1/fd/2\n" >> /etc/crontabs/root

COPY config.sample.ini /config/config.ini

VOLUME ["/config"]

CMD ["crond", "-f", "-d", "8"]
