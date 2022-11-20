FROM python:3.7-alpine

COPY  ["requirements.txt", "src", "/app/"]

RUN apk add --update --no-cache --virtual .build-deps gcc musl-dev git && \
    pip install -r /app/requirements.txt > /dev/null && \
    rm /app/requirements.txt && \
    ln -s /config/config.ini /app/config.ini && \
    apk del .build-deps && \
    printf "*/10 * * * * cd /app/ && python /app/main.py > /proc/1/fd/1 2> /proc/1/fd/2\n" >> /etc/crontabs/root

COPY config.sample.ini /config/config.ini

VOLUME ["/config"]

CMD ["crond", "-f", "-d", "8"]
