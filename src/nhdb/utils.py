from typing import Any, Sequence
from rich.logging import RichHandler
from logging import FileHandler, Handler, Logger, Formatter, StreamHandler
from enum import Enum
from NHentai.entities.doujin import Tag


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40


def makeLogger(
    loglevel: LogLevel,
    handler: Handler = None,
) -> Logger:
    logger = Logger(loglevel.value)
    handle = handler or RichHandler(
        show_time=True,
        show_path=False,
        show_level=True,
        markup=True,
        log_time_format="%H:%M:%S",
    )
    formatter = Formatter("[%(asctime)s | %(levelname)s] %(message)s", "%H:%M:%S")
    handle.setFormatter(formatter) if isinstance(
        handler, FileHandler | StreamHandler
    ) else ...
    logger.addHandler(handle)

    return logger


def massReplace(target: str, replaces: list[tuple[str, str]]) -> str:
    for before, after in replaces:
        target = target.replace(before, after)

    return target


def toPropertyName(prop: str) -> str:
    return massReplace(
        prop, [(char, "_") for char in " -!@#$%^&*()_+\{\}\\|;:'\"<,>./?`~"]
    ).lower()


def toTagName(data: Tag) -> str:
    # return data
    return f"{getattr(data, 'type')}:{getattr(data, 'name')}"


def toLogLevel(data: str) -> LogLevel:
    return LogLevel._member_map_.get(data.upper().strip())


def cleanseArgument(arg: str) -> str:
    """
    Default cleanse hook for the `CommandInterpreter` object
    """
    return massReplace(arg, [("\\", "")])


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
