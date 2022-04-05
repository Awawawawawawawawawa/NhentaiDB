from logging import FileHandler
from pathlib import Path
from sqlite3 import OperationalError
from rich.progress import Progress
from rich.console import Console
from textwrap import shorten
from nhdb import (
    ProjectConfig,
    SauceDB,
    LogLevel,
    CommandInterpreter,
    makeLogger,
    grabSauces,
)

DB_PATH = Path("./res/nh-index.sqlite")
LOG_PATH = Path("./logs/db-update.log")

console = Console()
db = SauceDB(DB_PATH)
mainLogger = makeLogger(LogLevel.INFO)
nhci = CommandInterpreter(mainLogger)


@nhci.command(["q", "exit", "quit"], True)
def quitApp():
    """
    Gracefully closes the program.
    Usage: [yellow]exit[/yellow] or [yellow]quit[/yellow]

    [bold red blink]NOTE:[/bold red blink]\t[u]^C[/u] and [u]^Z[/u] [i]might[/i] work, but this might cause
    \tproblems for the program later on, so it is highly recommended to use this command instead
    \tof [u]^C[/u] and [u]^Z[/u]
    """
    quit()


def getNextSauce() -> int:
    try:
        return max(db.getSauces("id")) + 1
    except ValueError:
        return 1


@nhci.command(["i", "sauce-update"], True)
def scanSauces():
    """
    Indexes doujins from [link=https://nhentai.net]nHentai.net[/link].
    Usage: [yellow]sauce-index[/yellow]

    [i]Since nh's doujin index is pretty large, do not be surprised if it takes forever to finish[/i]
    """
    indexLogger = makeLogger(LogLevel.INFO, FileHandler(LOG_PATH))
    with console.status(
        f"Updating Database. Please check {LOG_PATH!s} for the status",
        spinner="bouncingBar",
    ) as stat:
        for data in grabSauces(getNextSauce()):
            try:
                db.addSauce(
                    data.id,
                    data.title.english,
                    data.upload_date,
                    data.tags,
                    data.num_pages,
                    data.num_favorites,
                )
            except OperationalError as err:
                stat.stop()
                indexLogger.error(
                    "An Error Occurred. Please check the traceback for more information",
                    exc_info=1,
                )
                mainLogger.error(f"{err}, check {LOG_PATH!s} for the traceback")
                return

            indexLogger.info(
                f'Indexed "{data.title.pretty or shorten(data.title.english, 30)}" (https://nhentai.net/g/{data.id})'
            )


nhci.cmdloop()
