#!/bin/sh
# Start a local PostgreSQL 17 (database aidb, user ai/ai) when a case asks for
# one, point Maven at the egress proxy when the sandbox is on the allowlist
# network, then run the given command as the unprivileged agent user.
set -e
if [ "${GATE1_POSTGRES:-0}" = "1" ]; then
  PGBIN=/usr/lib/postgresql/17/bin
  install -d -o postgres /var/run/postgresql /tmp/pgdata
  su postgres -s /bin/sh -c "$PGBIN/initdb -D /tmp/pgdata -A trust >/dev/null && $PGBIN/pg_ctl -D /tmp/pgdata -l /tmp/pg.log -o '-c listen_addresses=localhost' -w start >/dev/null"
  su postgres -s /bin/sh -c "psql -U postgres -d postgres -qc \"CREATE ROLE ai LOGIN SUPERUSER PASSWORD 'ai'\" && createdb -U postgres -O ai aidb"
fi
# curl, git, npm, Node and the agents read HTTPS_PROXY; Maven (mvn and ./mvnw)
# reads only settings.xml. Written on every start: the .m2 volume is shared,
# and an open-network run must not inherit a proxy that is not there.
SETTINGS=/home/agent/.m2/settings.xml
if [ -n "${GATE1_PROXY_HOST:-}" ]; then
  cat > "$SETTINGS" <<EOF
<settings>
  <proxies>
    <proxy><id>gate1-https</id><active>true</active><protocol>https</protocol>
      <host>${GATE1_PROXY_HOST}</host><port>${GATE1_PROXY_PORT:-8888}</port>
      <nonProxyHosts>localhost|127.0.0.1</nonProxyHosts></proxy>
    <proxy><id>gate1-http</id><active>true</active><protocol>http</protocol>
      <host>${GATE1_PROXY_HOST}</host><port>${GATE1_PROXY_PORT:-8888}</port>
      <nonProxyHosts>localhost|127.0.0.1</nonProxyHosts></proxy>
  </proxies>
</settings>
EOF
  chown agent "$SETTINGS"
else
  rm -f "$SETTINGS"
fi
exec su agent -s /bin/sh -c 'cd /work && exec "$0" "$@"' -- "$@"
