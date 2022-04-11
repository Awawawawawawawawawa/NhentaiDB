# General Dependencies
from contextlib import suppress
from datetime import datetime
from logging import FileHandler
from os import remove
from sqlite3 import ProgrammingError
from textwrap import shorten
from threading import Thread
from inspect import stack
from typing import Any, Sequence
from atexit import register as atexit
from itertools import count

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
)
from nhdb.exceptions import ItemAlreadyExists
from nhdb.store import RecursiveNamespace

D_QUOTE = '"'

# Globals
terminal = Console()
config = loadConfig("./res/config.yml")
client = NHentai(config.nhentai.cache_limit)
database = SauceDB(config.paths.database)
mainLogger = makeLogger(LogLevel.INFO)
fileLogger = makeLogger(LogLevel.INFO, FileHandler(config.paths.runtime_logs))
app = CommandInterpreter(mainLogger)


@app.command(alias=["q", "exit", "quit"])
def quitApp():
    """
    Gracefully closes the program.

    [bold red blink]NOTE:[/bold red blink]\t[u]^C[/u] and [u]^Z[/u] [i]might[/i] work, but this might cause
    \tproblems for the program later on, so it is highly recommended to use this command instead
    \tof [u]^C[/u] and [u]^Z[/u]
    """
    broadcastMessageToLoggers("Goodbye!")
    quit()


@app.command(alias=["c", "clean"])
def clean():
    """
    Removes [bold cyan]files generated on program start[/bold cyan]

    This could be useful if your [green]database[/green] is locked
    """
    remove(config.paths.database)
    remove(config.paths.runtime_logs)
    broadcastMessageToLoggers("Remove Generated Files")
    broadcastMessageToLoggers("Please restart the program after the bye-bye message")
    quitApp()


@app.command(alias=["u", "sauce-update"])
def scanSauces():
    """
    Indexes doujins from [bold]nhentai.net[bold].

    [i]Since nh's doujin index is pretty large, do not be surprised if it takes forever to finish[/i]
    """
    broadcastMessageToLoggers("Updating database...")

    while terminal.status(
        f"Updating Database..., check [bold cyan]{config.paths.runtime_logs}[/bold cyan] for the status",
        spinner="bouncingBar",
    ):
        for chunk in chunkinate(count(getNextSauce()), 100):
            threads = [
                Thread(target=savedb, args=(id,), name=f"Doujin-Get::{id}")
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
        mainLogger.error(f"{key!r} is invalid")
        return

    print(key, value)


@app.command(alias=["l", "sauce-list"])
def listSauce():
    """
    Lists doujins stored in the [green]database[/green]
    """
    # print(database.empty)

    if database.empty:
        mainLogger.error(
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

    fileLogger.info(
        f'Adding "{(data.title.pretty or shorten(data.title.english, 20)).strip(D_QUOTE)}" (#{data.id})'
    )

    try:
        database.addSauce(
            data.id,
            data.title,
            data.upload_at,
            data.tags,
            data.total_pages,
            data.total_favorites,
        )
        fileLogger.info(f"Added #{data.id} to database")
        database.commit()

        fileLogger.info(f"Committed #{data.id} to database")
    except ItemAlreadyExists:
        mainLogger.error(f"Doujin {id} already exists!")


def getNextSauce() -> int:
    try:
        return max(database.getSauces("id")) + 1
    except ValueError:
        return 1


def dissectTag(rawTagData: str):
    for tag in rawTagData.split(";"):
        yield from tag.split(":")


def chunkinate(data: Sequence[Any], chunkSize: int = 1000):
    # sourcery skip: for-append-to-extend
    dataIter = iter(data)
    while True:
        chunk = []
        try:
            for _ in range(chunkSize):
                chunk.append(next(dataIter))
            yield chunk
        except StopIteration:
            if chunk:
                yield chunk
            break


def broadcastMessageToLoggers(
    msg: str, level: LogLevel = LogLevel.INFO, showTraceback: bool = False
):
    funcName = stack()[1].function
    mainLogger.log(level.value, msg, exc_info=showTraceback)
    fileLogger.log(
        level.value, f"[Broadcasted from {funcName}] {msg}", exc_info=showTraceback
    )


@atexit
def programExit():
    try:
        database.close()
        broadcastMessageToLoggers("Database is closed")
    except ProgrammingError:
        broadcastMessageToLoggers("Databased is closed! How?", LogLevel.ERROR)
    broadcastMessageToLoggers("Exiting...")


def main():
    while True:
        with suppress(KeyboardInterrupt):
            app.cmdloop()


if __name__ == "__main__":
    main()
