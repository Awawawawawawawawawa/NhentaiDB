# General Dependencies
from contextlib import suppress
from datetime import datetime
from os import remove
from sqlite3 import ProgrammingError
from threading import Thread
from typing import Any, Sequence
from atexit import register as atexit
from itertools import count

# import gnureadline

# Rich Components
from rich.table import Table
from rich.console import Console
from rich import print

# NHentai API
from NHentai.nhentai import NHentai

# NH-DB Components
from nhdb import (
    loadConfig,
    SauceDB,
    LogLevel,
    CommandInterpreter,
    makeLogger,
    dissectTag,
    chunkinate,
)
from nhdb.exceptions import ItemAlreadyExists


# Globals
config = loadConfig("./res/config.yml")
console = Console(record=config.console.record)
client = NHentai(config.nhentai.cache_limit)
database = SauceDB(config.paths.database)
logger = makeLogger(LogLevel.INFO)
app = CommandInterpreter(logger)


@app.command(alias=["q", "exit", "quit"])
def quitApp():
    """
    Gracefully closes the program.

    [bold red blink]NOTE:[/bold red blink]\t[u]^C[/u] and [u]^Z[/u] [i]might[/i] work, but this might cause
    \tproblems for the program later on, so it is highly recommended to use this command instead
    \tof [u]^C[/u] and [u]^Z[/u]
    """
    logger.info("Goodbye!")
    quit()


@app.command(alias=["c", "clean"])
def clean():
    """
    Removes [bold cyan]files generated on program start[/bold cyan]

    This could be useful if your [green]database[/green] is locked
    """
    remove(config.paths.database)
    remove(config.paths.runtime_logs)
    logger.info("Removed Generated Files")
    logger.info("Please restart the program after the bye-bye message")
    quitApp()


@app.command(alias=["u", "sauce-update"])
def scanSauces():
    """
    Indexes doujins from [bold]nhentai.net[bold].

    [i]Since nh's doujin index is pretty large, do not be surprised if it takes forever to finish[/i]
    """
    logger.info("Updating database...")

    while console.status(
        f"Updating Database..., check [bold cyan]{config.paths.runtime_logs}[/bold cyan] for the status",
        spinner="bouncingBar",
    ):
        for chunk in chunkinate(count(database.getNextId()), 10):
            threads = [
                Thread(target=savedb, args=(id,), name=f"Doujin-Get::{id}", daemon=False)
                for id in chunk
            ]

            for thread in threads:
                thread.start()


@app.command(alias=["g", "sauce-get"])
def getSauce(key: str, value: int):
    """
    Grabs doujin/s by [magenta bold underline]name, id, tags, page and favorite count[/magenta bold underline]

    Examples:
        g id 2020
        sauce-get tag big boobs
    """
    if key not in database.columns:
        logger.error(f"{key!r} is invalid")
        return

    print(key, value)


@app.command(alias=["l", "sauce-list"])
def listSauce():
    """
    Lists doujins stored in the [green]database[/green]
    """
    if database.empty:
        logger.error(
            "Database is empty! Run [magenta bold]sauce-update[/magenta bold] to index NHentai"
        )
        return

    res = Table("ID", "Title", "Uploaded On", "Tags", "Pages", "Favorites")

    for id, title, uploaded, tags, pages, faves in database.getSauces():
        tags = str(filter(lambda key, val: key == "tag", dissectTag(tags)))
        id = str(id)
        pages = str(pages)
        faves = str(faves)
        uploaded = datetime.fromtimestamp(uploaded).strftime("%A, %d %b %Y")

        res.add_row(
            id,
            title,
            uploaded,
            tags,
            pages,
            faves,
        )

    print(res)


def savedb(id: int):
    data = client.get_doujin(str(id))

    try:
        database.addSauce(
            data.id,
            data.title,
            data.upload_at,
            data.tags,
            data.total_pages,
            data.total_favorites,
        )
        database.commit()
    except ItemAlreadyExists:
        logger.error(f"Doujin {id} already exists!")
    except Exception:
        console.print_exception(show_locals=True)


@atexit
def programExit():
    try:
        database.close()
    except ProgrammingError:
        logger.error("Databased is closed! How?")
    logger.info("Exiting...")


def main():
    while True:
        with suppress(KeyboardInterrupt, EOFError):
            app.cmdloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        from datetime import datetime
        from rich.terminal_theme import *

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"nhdb-crash-{now}.svg"

        logger.error("Uh Oh!")
        console.print_exception()
        console.save_svg(filename, theme=MONOKAI, title=filename.split(".")[0])
        logger.info(
            f"Exported record of the console output to [underline cyan]{filename}[/underline cyan]. Please send this to the developer"
        )
