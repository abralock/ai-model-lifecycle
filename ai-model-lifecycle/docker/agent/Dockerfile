# Gate 1 agentic sandbox: Claude Code plus the toolchains the cases need,
# so the agent can build, test and fix its own work (agentic.py).
#   Java 17 + Maven       r1, r1b
#   Node 20 + Chromium    r1b (Cypress), r2 (Angular)
#   PostgreSQL 17         r3, r4, r5 (started by the entrypoint)
#   Java 8 (/opt/java8)   r2: the original GWT app's App Engine dev server
# Model-written code runs only in here; the workspace is the one mount it can write.
FROM node:20.18.0-bookworm-slim AS node
FROM eclipse-temurin:8-jdk AS java8

FROM debian:bookworm-slim
ARG CLAUDE_CODE_VERSION=2.1.316
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git gnupg less procps python3 unzip xz-utils \
        openjdk-17-jdk-headless maven \
        chromium xvfb xauth libgtk-3-0 libnotify4 libgbm1 libnss3 libxss1 libasound2 libxtst6 \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends postgresql-17 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=java8 /opt/java/openjdk /opt/java8
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
    && npm cache clean --force
# opencode, the agent for open-weight models (OpenCode Go). v2 is not on npm
# (npm `opencode-ai` is still v1, without /goal): the pinned GitHub release
# binary, checked against the release's SHA256SUMS. A build-time run leaves
# root-owned state (/tmp/opencode is its temp dir), which the agent user
# could not write to, so it is removed.
ARG OPENCODE_VERSION=2.2.5
RUN case "$(dpkg --print-architecture)" in \
        arm64) plat=linux-arm64 ;; amd64) plat=linux-x64 ;; \
        *) echo "no opencode build for $(dpkg --print-architecture)" >&2; exit 1 ;; \
    esac \
    && mkdir /tmp/oc-dl && cd /tmp/oc-dl \
    && base="https://github.com/anomalyco/opencode/releases/download/v${OPENCODE_VERSION}" \
    && curl -fsSLO "$base/opencode-$plat.tar.gz" && curl -fsSLO "$base/SHA256SUMS" \
    && grep " opencode-$plat.tar.gz\$" SHA256SUMS | sha256sum -c - \
    && tar xzf "opencode-$plat.tar.gz" && install -m 755 opencode /usr/local/bin/opencode \
    && cd / && rm -rf /tmp/oc-dl \
    && test "$(opencode --version)" = "opencode v${OPENCODE_VERSION}" \
    && rm -rf /tmp/opencode /root/.local/share/opencode /root/.cache/opencode \
              /root/.config/opencode /root/.local/state/opencode
LABEL gate1.claude_code.version=$CLAUDE_CODE_VERSION gate1.opencode.version=$OPENCODE_VERSION
# Claude Code refuses to skip permission prompts as root; the agent is a plain user.
RUN useradd -m -s /bin/bash agent && install -d -o agent /work /home/agent/.m2 /home/agent/.npm
ENV CHROME_BIN=/usr/bin/chromium JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64 \
    PGHOST=localhost PGPORT=5432 PGUSER=ai PGPASSWORD=ai PGDATABASE=aidb \
    POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_USER=ai POSTGRES_PASSWORD=ai POSTGRES_DB=aidb
COPY entrypoint.sh /usr/local/bin/gate1-agent-entrypoint
RUN chmod 755 /usr/local/bin/gate1-agent-entrypoint
WORKDIR /work
ENTRYPOINT ["/usr/local/bin/gate1-agent-entrypoint"]
