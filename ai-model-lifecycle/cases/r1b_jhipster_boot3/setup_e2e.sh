#!/usr/bin/env bash
# One-time setup for the R1b end-to-end check (re-run is a no-op).
#
# The scorer needs the app's unchanged Angular frontend, prebuilt, and its
# Cypress suite with node_modules. Neither lives in git (about 1.5 GB):
#   $GATE1_CACHE/r1b_jhipster_boot3/frontend   (default GATE1_CACHE: ~/.cache/ai-model-lifecycle)
#
# Needs: git, Node 16.17+ / npm, Google Chrome (Cypress runs with --browser chrome).
set -euo pipefail

# Our fork of jhipster/jhipster-sample-app, at tag v7.9.3's commit (a fork has
# no tags, so pin the commit; it is the one in cases/sources.lock.json).
REPO=https://github.com/abralock/jhipster-sample-app
COMMIT=7d39dfaa9edeae5ba8322bb44b7d7487764ef934
CACHE="${GATE1_CACHE:-$HOME/.cache/ai-model-lifecycle}/r1b_jhipster_boot3"
DIR="$CACHE/frontend"

mkdir -p "$CACHE"
if [ ! -d "$DIR/.git" ]; then
  git init --quiet "$DIR"
  git -C "$DIR" fetch --quiet --depth 1 "$REPO" "$COMMIT"
  git -C "$DIR" checkout --quiet FETCH_HEAD
fi
cd "$DIR"
[ -x node_modules/.bin/cypress ] || npm ci --no-audit --no-fund
npx cypress verify >/dev/null || echo "warning: cypress verify failed or timed out (it can on a busy machine); the first run re-verifies"
# Production Angular build -> target/classes/static, copied into the jar by the scorer.
[ -f target/classes/static/index.html ] || npm run webapp:build:prod
echo "r1b e2e cache ready: $DIR"
