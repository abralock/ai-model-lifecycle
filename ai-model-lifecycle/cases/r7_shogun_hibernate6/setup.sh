#!/bin/sh
# Build r7's Maven cache: the original shogun-core's whole dependency closure,
# resolved by building and testing the untouched project once with Java 8.
#
#   sh cases/r7_shogun_hibernate6/setup.sh      (from ai-model-lifecycle/; Docker running)
#
# shogun-core resolves through terrestris's Nexus (its pom lists it before
# Maven Central), and three of its libraries exist only there: gt-main 22.2,
# deegree-core-commons 3.4.11 and structured-content-tools 1.3.11. The agent
# sandbox cannot reach that host, so agentic.py (_setup_r7) seeds this cache
# into the sandbox's Maven volume, and the scorer builds against a copy of it.
#
# Output: $GATE1_CACHE/r7_shogun_hibernate6/m2 (default ~/.cache/ai-model-lifecycle).
# Takes about 20-25 minutes the first time (mostly downloads); a no-op after.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
cache="${GATE1_CACHE:-$HOME/.cache/ai-model-lifecycle}/r7_shogun_hibernate6"
m2="$cache/m2"
if [ -d "$m2/org/geotools/gt-main/22.2" ] && [ -f "$cache/original-tests.txt" ]; then
    echo "r7 cache ready: $m2 ($(cat "$cache/original-tests.txt"))"
    exit 0
fi
# the pinned sources (cases/sources.lock.json)
(cd "$here/../.." && python -m cases.sources r7_shogun_hibernate6)
mkdir -p "$m2"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp -R "$here/project/." "$work/"
docker run --rm -v "$work:/w" -v "$m2:/root/.m2/repository" -w /w \
    maven:3.8-openjdk-8 mvn -B -ntp -pl shogun-core-main -am verify | tee "$work/build.log" | tail -20
total=$(grep -E '^\[INFO\] Tests run: [0-9]+, Failures: 0, Errors: 0, Skipped: 0$' "$work/build.log" | tail -1)
[ -n "$total" ] || { echo "the original build did not pass all its tests" >&2; exit 1; }
echo "$total" | sed 's/^\[INFO\] //' > "$cache/original-tests.txt"
echo "r7 cache ready: $m2 ($(cat "$cache/original-tests.txt"))"
