#!/bin/sh
# Start a local PostgreSQL 17 (database aidb, user ai/ai) when a case asks for
# one, then run the given command as the unprivileged agent user.
set -e
if [ "${GATE1_POSTGRES:-0}" = "1" ]; then
  PGBIN=/usr/lib/postgresql/17/bin
  install -d -o postgres /var/run/postgresql /tmp/pgdata
  su postgres -s /bin/sh -c "$PGBIN/initdb -D /tmp/pgdata -A trust >/dev/null && $PGBIN/pg_ctl -D /tmp/pgdata -l /tmp/pg.log -o '-c listen_addresses=localhost' -w start >/dev/null"
  su postgres -s /bin/sh -c "psql -U postgres -d postgres -qc \"CREATE ROLE ai LOGIN SUPERUSER PASSWORD 'ai'\" && createdb -U postgres -O ai aidb"
fi
exec su agent -s /bin/sh -c 'cd /work && exec "$0" "$@"' -- "$@"
