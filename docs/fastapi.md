# FastAPI

The application uses [FastAPI](https://fastapi.tiangolo.com/) to expose a REST API. Run

```console
uv run fastapi dev
```

to start the dev server.

## FastAPI Cloud

The application is deployed to [FastAPI Cloud](https://fastapicloud.com/) with

```console
uv run fastapi deploy
```

Once deployed, the application should be accessible at [https://agora.fastapicloud.dev/](https://agora.fastapicloud.dev/).

### Environment variables

The proper environment variables must be defined in the dashboard for the app on [FastAPI Cloud](https://dashboard.fastapicloud.com/jonasrenault-6084648e/apps/agora/environment-variables) by copying the `.env` file.

### Chromium drivers

The FastAPI app has a lifespan context manager which runs the command `playwright install chromium` when the FastAPI app is started, ensuring that the drivers are available on the web app.

## Configuration

The entrypoint for the FastAPI app is defined in `pyproject.toml`:

```toml
[tool.fastapi]
entrypoint = "agora.api.main:app"
```
