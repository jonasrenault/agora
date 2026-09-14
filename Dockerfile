FROM python:3.12-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /uvx /bin/

# Install Playwright browsers and system dependencies
# version here must match the one in pyproject.toml to ensure browser versions match
RUN uvx patchright@1.61.2 install --with-deps chromium

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1
# Disable development dependencies
ENV UV_NO_DEV=1
# Enable caching
ENV UV_LINK_MODE=copy

# Change the working directory to the `app` directory
WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,id=s/fedbe1ac-3dfe-4f25-828e-4fa18645a666-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy the project into the image
COPY . /app

# Sync the project
RUN --mount=type=cache,id=s/fedbe1ac-3dfe-4f25-828e-4fa18645a666-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "agora.api.main:app", "--host", "0.0.0.0", "--port", "8080","--proxy-headers", "--forwarded-allow-ips", "*"]

# Run the web service on container startup.
# CMD ["hypercorn", "agora.api.main:app", "--bind", "::"]
