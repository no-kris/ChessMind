FROM python:3.13-slim

# System tools, agent tools, and Stockfish
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    procps \
    nano \
    ripgrep \
    jq \
    stockfish \
    && rm -rf /var/lib/apt/lists/*

# Node 22 LTS (includes npm)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Claude Code
RUN npm install -g @anthropic-ai/claude-code

ENV STOCKFISH_PATH=/usr/games/stockfish \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

# Claude Code configuration: settings + status line
RUN mkdir -p /root/.claude
COPY settings.json /root/.claude/settings.json
COPY statusline.sh /root/.claude/statusline.sh
RUN sed -i 's/\r$//' /root/.claude/statusline.sh \
    && chmod +x /root/.claude/statusline.sh

# Entrypoint (restores Claude login from the claude-auth volume)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /workspace
EXPOSE 8000 5173

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["bash", "-c", "\
    cd /workspace/backend && uv sync; \
    cd /workspace/frontend && [ package-lock.json -nt node_modules/.package-lock.json ] && npm ci; \
    cd /workspace && exec bash"]
