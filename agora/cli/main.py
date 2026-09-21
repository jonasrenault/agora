import asyncio
import logging

import typer
from rich.logging import RichHandler

from agora.automation import book_dates

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
    asyncio.run(book_dates())


if __name__ == "__main__":
    app()
