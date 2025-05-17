FROM python:3.11-alpine
LABEL maintainer="vittigupta"
ENV PYTHONUNBUFFERED=1
ARG DEV=false

COPY ./requirements.txt /tmp/requirements.txt
COPY ./scripts  /scripts
COPY . /app
WORKDIR /app
EXPOSE 8000


RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && apk add --no-cache --virtual .build-deps \
         build-base postgresql-dev musl-dev zlib-dev linux-headers \
    && /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && if [ "$DEV" = "true" ] ; then /venv/bin/pip install pytest pytest-django; fi \
    && apk del .build-deps \
    && rm -rf /tmp/requirements.txt /var/cache/apk/* \
    && adduser -D django \
    && mkdir -p /vol/web/static \
    && chown -R django:django /app /scripts /vol \
    && chmod -R 755 /vol \
    && apk add --no-cache su-exec dos2unix \
    && dos2unix /scripts/*.sh \
    && chmod +x /scripts/entrypoint.sh /scripts/run.sh

ENV PATH="/scripts:/venv/bin:$PATH"

USER root
ENTRYPOINT ["/scripts/entrypoint.sh"]
CMD ["/scripts/run.sh"]