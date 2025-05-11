FROM python:3.11-alpine
LABEL maintainer="vittigupta"
ENV PYTHONUNBUFFERED=1
ARG DEV=false

# Install & cache dependencies
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && apk add --no-cache --virtual .build-deps \
         build-base postgresql-dev musl-dev zlib-dev linux-headers \
    && /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && if [ "$DEV" = "true" ] ; then /venv/bin/pip install pytest pytest-django; fi \
    && apk del .build-deps \
    && rm -rf /tmp/requirements.txt /var/cache/apk/*

# Copy project code
COPY . /app
WORKDIR /app

# Create non-root user
RUN adduser -D django \
    && chown -R django:django /app

USER django
ENV PATH="/venv/bin:$PATH"
EXPOSE 8000

# Wait for DB, migrate, collectstatic, then run dev server
CMD ["sh", "-c", "python manage.py wait_for_db && python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]