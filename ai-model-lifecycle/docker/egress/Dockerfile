# Gate 1 sandbox egress: the only way out of the agent sandbox (agentic.py).
# Agent containers sit on an internal Docker network with no route to the
# internet; this proxy, on that network and the default bridge, forwards only
# to the hosts in allowlist.txt (the model APIs and the package registries a
# build needs) and logs every request, allowed or refused.
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends tinyproxy \
    && rm -rf /var/lib/apt/lists/*
COPY tinyproxy.conf /etc/tinyproxy/tinyproxy.conf
COPY allowlist.txt /etc/tinyproxy/allowlist.txt
EXPOSE 8888
USER tinyproxy
ENTRYPOINT ["tinyproxy", "-d", "-c", "/etc/tinyproxy/tinyproxy.conf"]
