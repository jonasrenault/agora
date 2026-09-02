import asyncio
import logging

import typer
from rich.logging import RichHandler

from agora.agora import book_agora
from agora.api.google.gmail import read_emails

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True)]
)
app = typer.Typer(no_args_is_help=True)


@app.command()
def book():
    """
    Book a slot.
    """
    asyncio.run(book_agora())


@app.command()
def gmail():
    read_emails()


if __name__ == "__main__":
    app()
