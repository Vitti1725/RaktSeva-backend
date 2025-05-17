#!/bin/sh
set -e

mkdir -p /vol/web/static
chown -R django:django /vol/web/static

exec su-exec django "$@"
