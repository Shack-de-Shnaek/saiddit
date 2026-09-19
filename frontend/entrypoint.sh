#!/bin/sh
set -e

# Fail fast on a broken config instead of starting a half-working server.
nginx -t

# Serve the built frontend from /usr/share/nginx/html in the foreground.
exec nginx -g 'daemon off;'
