# Docker

The application provides a Dockerfile to build an image for deployment. It installs the [dependencies required to run Playwright](https://docs.railway.com/guides/playwright) as well as the FastApi app.

## Docker compose

A docker compose file is provide to run the app using docker for development. Run

```console
docker compose watch
```

to start the application.
