#!/bin/sh
# Render provides a PORT environment variable that we must use.
# Default to 8069 if PORT is not set (for local execution).
ODOO_HTTP_PORT=${PORT:-8069}

# Resolve database host – if the provided DB_HOST cannot be resolved (e.g. Render hostname on local), fallback to 'db'
RESOLVED_HOST=${DB_HOST:-}
if ! getent hosts "$RESOLVED_HOST" >/dev/null 2>&1; then
  echo "[entrypoint] DB_HOST '$RESOLVED_HOST' not resolvable – falling back to 'db'"
  RESOLVED_HOST="db"
fi

# Override environment so subprocess sees correct host
export DB_HOST="$RESOLVED_HOST"

# Cài packages Python nếu có requirements.txt
if [ -f /etc/odoo/requirements.txt ]; then
  echo "[entrypoint] Installing Python packages from /etc/odoo/requirements.txt"
  python3 -m pip install --no-cache-dir -r /etc/odoo/requirements.txt || echo "[entrypoint] pip install failed (continuing)"
fi

# Build optional args for dev and update behavior
DEV_ARGS=""
if [ "${DEV_MODE}" = "1" ] || [ "${DEV_MODE}" = "true" ]; then
  # reload python, auto-reload qweb/xml in dev
  DEV_ARGS="--dev=reload,qweb,xml"
fi

UPDATE_ARGS=""
if [ -n "${AUTO_UPDATE}" ]; then
  # e.g., AUTO_UPDATE=p2p_bridge or AUTO_UPDATE=module1,module2
  UPDATE_ARGS="-u ${AUTO_UPDATE}"
fi

odoo -c /etc/odoo/odoo.conf \
     --http-port $ODOO_HTTP_PORT \
     --http-interface 0.0.0.0 \
     --db_host ${DB_HOST:-localhost} \
     --db_port ${DB_PORT:-5432} \
     --db_user ${DB_USER:-odoo} \
     --db_password ${DB_PASSWORD:-odoo} \
     --database ${DB_DATABASE:-odoo} \
     ${DEV_ARGS} ${UPDATE_ARGS}