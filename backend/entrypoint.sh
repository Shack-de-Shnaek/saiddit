#!/bin/sh
set -e

# Apply existing migrations before the app starts serving requests.
python src/manage.py migrate --noinput

# Hand PID 1 over to the CMD (gunicorn) so it receives stop signals directly.
exec "$@"
