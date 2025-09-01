#!/bin/sh
set -e

# allow overriding project dir and settings
: "${DJANGO_PROJECT_DIR:=/app/propbench}"
: "${DJANGO_SETTINGS_MODULE:=propbench.settings}"
: "${DJANGO_SQLITE_PATH:=/data/db.sqlite3}"

export DJANGO_SETTINGS_MODULE
export PYTHONPATH="${DJANGO_PROJECT_DIR}:${PYTHONPATH:-}"

echo "Using project dir: ${DJANGO_PROJECT_DIR}"
cd "${DJANGO_PROJECT_DIR}"

# run migrations and collectstatic (idempotent)
echo "Running migrations..."
python manage.py migrate --noinput || true

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Ensure DB file (if used in /data) is writable for container user (best-effort)
if [ -f "${DJANGO_SQLITE_PATH}" ]; then
  echo "Adjusting permissions on ${DJANGO_SQLITE_PATH}"
  chmod 664 "${DJANGO_SQLITE_PATH}" || true
fi

exec "$@"