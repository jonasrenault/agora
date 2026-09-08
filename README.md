# Agora

Custom application to book activity slots on [Agora Portail Famille](https://www.agoraplus.fr/agora-famille/#).

## Installation

Clone the repository and install the project using [uv](https://docs.astral.sh/uv/)

```console
git clone git@github.com:jonasrenault/agora.git
cd agora
uv sync
```

## Setup

The application uses [Playwright](https://playwright.dev/python/) / [Patchwright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) to manage browser interactions. This requires a chromium driver to be installed on the machine. Run

```console
# Install Chromium-Driver for Patchright
playwright install chromium
```

### Configuration

Configuration is managed with [pydantic-settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/) in the [config.py](./agora/config/config.py) module.

Set the required Env variables in a `.env` file in the root directory of the project. For example, add the following to [.env](./.env)

```.env
AGORA_EMAIL=hello@test.com
AGORA_PASSWORD=mysecretpwd
FASTAPI_ENV=development
PROJECT_NAME="Agora API"
SECRET_KEY=3e9429d6b2e7f3c576e74c428edd6677952328bb9bbd9516edc300c236bae3d3
ADMIN_PASSWORD=anothersecretpwd
```

## FastAPI

The application uses [FastAPI](https://fastapi.tiangolo.com/). Run

```console
uv run fastapi dev
```

to start the dev server.
