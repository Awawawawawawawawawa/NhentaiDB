from pathlib import Path
from contextlib import suppress
from sqlite3 import connect, Connection, OperationalError
from typing import Any
from yaml import load, Loader
from .utils import toPropertyName, toTagName


class SauceDB:
    def __init__(self, file: Path = None) -> None:
        self.file = file
        self.connection = connect(file or ":memory:")
        self.database = self.connection.cursor()

        with suppress(OperationalError):
            self.database.execute(
                "CREATE TABLE sauces (id int, title text, uploaded datetime, tags text, pages tinyint, favorites int)"
            )

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def __enter__(self) -> Connection:
        return self.connection

    def __exit__(self, *err):
        del self

    def columns():
        return ("id", "title", "uploaded", "tags", "pages", "favorites")

    def addSauce(
        self,
        id: int,
        title: str,
        uploaded: int,
        tags: list,
        pages: int,
        favorites: int,
    ):
        self.database.execute(
            "INSERT INTO sauces VALUES (?, ?, ?, ?, ?, ?)",
            (id, title, uploaded, ";".join(map(toTagName, tags)), pages, favorites),
        )

    def getSauces(self, *columns):
        # print(f"SELECT {', '.join(columns) or '*'} FROM sauces")
        # return ""
        yield from self.database.execute(
            f"SELECT {', '.join(columns) or '*'} FROM sauces"
        )


class RecursiveNamespace:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(
                self,
                k,
                RecursiveNamespace(**v)
                if isinstance(v, dict)
                else [RecursiveNamespace(**element) for element in v]
                if isinstance(v, list | tuple) and isinstance(v[0], dict)
                else v,
            )

    def get(self, __k: str) -> Any:
        return getattr(self, __k)


class ProjectConfig:
    def __init__(self, file: Path) -> None:
        with open(file) as f:
            for name, value in load(f, Loader).items():
                setattr(self, toPropertyName(name), value)
