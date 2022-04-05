from rich.logging import RichHandler
from logging import Handler, Logger, Formatter
from enum import Enum


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40


def makeLogger(loglevel: LogLevel, handler: Handler = None):
    logger = Logger(loglevel.value)
    handle = handler or RichHandler(
        loglevel.value, show_time=True, show_level=True, markup=True
    )

    # handle.setFormatter(format)
    logger.addHandler(handle)

    return logger


def massReplace(target: str, replaces: list[tuple[str, str]]):
    for before, after in replaces:
        target = target.replace(before, after)

    return target


def toPropertyName(prop: str):
    return massReplace(
        prop, [(char, "_") for char in " -!@#$%^&*()_+\{\}\\|;:'\"<,>./?`~"]
    ).lower()


def toTagName(data: dict):
    # return data
    return f"{data.get('type')}:{data.get('name')}"
