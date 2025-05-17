FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer='vgdeveloper.com'

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV LISTEN_PORT=8000
ENV APP_HOST=web
ENV APP_PORT=9000

USER root

RUN mkdir -p /vol/static \
 && chmod 755 /vol/static \
 && apk add --no-cache dos2unix \
 && touch /etc/nginx/conf.d/default.conf \
 && chown nginx:nginx /etc/nginx/conf.d/default.conf \
 && dos2unix /run.sh \
 && chmod +x /run.sh \
 && apk del dos2unix

VOLUME /vol/static

USER nginx

CMD ["/run.sh"]