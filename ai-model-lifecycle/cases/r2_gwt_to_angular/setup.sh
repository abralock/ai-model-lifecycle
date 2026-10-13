#!/usr/bin/env bash
# One-time setup for the R2 scorer (re-run is a no-op). Builds, outside git:
#   $GATE1_CACHE/r2_gwt_to_angular/    (default GATE1_CACHE: ~/.cache/ai-model-lifecycle)
#     carstore-war/  the original GWT app (GWTP-Samples carstore @ 7dce06a), GWT-compiled
#                    with debug ids on; it also serves the REST API the Angular port calls
#     gae-sdk/       App Engine Java SDK 1.9.17, whose dev server runs that war
#     deps/          node_modules for the fixed Angular 18 workspace (workspace/package-lock.json)
#     e2e/           Playwright for the parity suite (scorers/fixtures/r2_parity/)
#
# Needs: git, docker, curl, unzip, Google Chrome (Playwright uses the installed Chrome).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CACHE="${GATE1_CACHE:-$HOME/.cache/ai-model-lifecycle}/r2_gwt_to_angular"
COMMIT=7dce06a                       # last carstore on a released GWTP (1.5); HEAD needs 2.0-SNAPSHOT
NODE_IMAGE=node:20.18.0-bookworm-slim
JAVA8_IMAGE=maven:3.8-openjdk-8
mkdir -p "$CACHE"

if [ ! -d "$CACHE/gae-sdk/appengine-java-sdk-1.9.17" ]; then
  mkdir -p "$CACHE/gae-sdk"
  curl -sfL -o "$CACHE/gae-sdk/sdk.zip" \
    https://repo1.maven.org/maven2/com/google/appengine/appengine-java-sdk/1.9.17/appengine-java-sdk-1.9.17.zip
  (cd "$CACHE/gae-sdk" && unzip -q sdk.zip && rm sdk.zip)
fi

if [ ! -f "$CACHE/carstore-war/CarStore.html" ]; then
  SRC="$CACHE/src/GWTP-Samples"
  [ -d "$SRC/.git" ] || git clone --quiet https://github.com/ArcBees/GWTP-Samples "$SRC"
  git -C "$SRC" checkout --quiet "$COMMIT"
  # integration-test profile = the IntegrationTesting GWT module, which keeps the
  # debug ids (id="gwt-debug-...") the parity suite selects on
  docker run --rm -v "$SRC/carstore":/src -v gate1_m2_j8:/root/.m2 -w /src "$JAVA8_IMAGE" \
    mvn -B -q -Pintegration-test -DskipTests -Dgwt.localWorkers=1 -Dgwt.extraJvmArgs=-Xmx1g package
  rm -rf "$CACHE/carstore-war"
  cp -a "$SRC/carstore/target/carstore-1.5" "$CACHE/carstore-war"
  rm -rf "$CACHE/carstore-war/WEB-INF/appengine-generated"
fi

# The Angular port is served at /ng/ from the same war. web.xml only lists
# CarStore.html as a welcome file, so /ng/ answered 403 and no port could pass:
# add index.html after it (/ still serves CarStore.html, which is tried first).
WEBXML="$CACHE/carstore-war/WEB-INF/web.xml"
if ! grep -q "<welcome-file>index.html</welcome-file>" "$WEBXML"; then
  sed -i 's#<welcome-file>CarStore.html</welcome-file>#&\n        <welcome-file>index.html</welcome-file>#' "$WEBXML"
fi

if [ ! -d "$CACHE/deps/node_modules/@angular/cli" ]; then
  mkdir -p "$CACHE/deps"
  cp "$HERE/workspace/package.json" "$HERE/workspace/package-lock.json" "$CACHE/deps/"
  docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$CACHE/deps":/w -w /w "$NODE_IMAGE" \
    npm ci --no-audit --no-fund
fi

if [ ! -d "$CACHE/e2e/node_modules/@playwright/test" ]; then
  mkdir -p "$CACHE/e2e"
  printf '{ "name": "r2-parity", "private": true, "devDependencies": { "@playwright/test": "1.47.2" } }\n' \
    > "$CACHE/e2e/package.json"
  (cd "$CACHE/e2e" && npm install --no-audit --no-fund)
fi

echo "r2 cache ready: $CACHE"
