# Docker

The application provides a Dockerfile to build an image for deployment. It installs the [dependencies required to run Playwright](https://docs.railway.com/guides/playwright) as well as the app.

## Docker compose

A docker compose file is provided to run the app using docker for development. Run

```console
docker compose watch
```

to start the application.

The docker compose file also includes a redis service. Change the value of `REDIS_URL` in the `.env` file to `redis://redis:6379` to use the local redis instance instead of redis cloud.
