from datetime import datetime
from pathlib import Path
from contextlib import suppress
from sqlite3 import ProgrammingError, connect, Connection, OperationalError
from typing import Any
from yaml import load, Loader
from NHentai.entities.doujin import Tag, Title

from rich.tree import Tree

from .utils import toPropertyName, toTagName
from .exceptions import ItemAlreadyExists


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
        with suppress(ProgrammingError):
            self.connection.commit()
            self.connection.close()

    def __enter__(self) -> Connection:
        return self.connection

    def __exit__(self, *err):
        with suppress(ProgrammingError):
            self.connection.commit()
            self.connection.close()

    @property
    def columns(self):
        return ("id", "title", "uploaded", "tags", "pages", "favorites")

    @property
    def empty(self):
        return bool(self.getSauces("id"))

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.commit()
        self.connection.close()

    def addSauce(
        self,
        id: int,
        title: Title,
        uploaded: datetime,
        tags: list[Tag],
        pages: int,
        favorites: int,
    ):
        # Check if our doujin already exists
        if self.getByID(id):
            raise ItemAlreadyExists(f"Doujin #{id} already exists!")

        self.database.execute(
            "INSERT INTO sauces VALUES (?, ?, ?, ?, ?, ?)",
            (
                id,
                title.pretty or title.english,
                (uploaded - datetime(1970, 1, 1)).total_seconds(),
                ";".join(map(toTagName, tags)),
                pages,
                favorites,
            ),
        )

    def getByID(self, id: int) -> tuple:
        # return tuple(filter(lambda i: i[0] == id, self.getSauces()))
        return self.database.execute(
            "SELECT id FROM sauce WHERE id = ?", (id,)
        ).fetchone()

    def getNextId(self) -> int:
        return self.database.execute("SELECT COUNT(id) FROM sauces").fetchone()[0]

    def getSauces(self, *columns):
        yield from self.database.execute(
            f"SELECT {', '.join(columns) or '*'} FROM sauces"
        )


class RecursiveNamespace:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(
                self,
                toPropertyName(k),
                RecursiveNamespace(**v)
                if isinstance(v, dict)
                else [RecursiveNamespace(**element) for element in v]
                if isinstance(v, list | tuple) and isinstance(v[0], dict)
                else v,
            )

    def __repr__(self) -> str:
        return "RecursiveNamespace(%s)" % ", ".join(
            ["=".join((k, repr(v))) for k, v in self.__dict__.items()]
        )

    def get(self, __k: str) -> Any:
        return getattr(self, __k)


def loadConfig(file: Path) -> RecursiveNamespace:
    with open(file) as f:
        with suppress(AttributeError):
            return RecursiveNamespace(**load(f, Loader))


def renderTree(
    namespace: RecursiveNamespace, parent: Tree = None, recursing: bool = False
) -> Tree:
    """
    Fun little function to view the namespace tree

    `parent` and `recursing` should not be passed

    Parameters
    ----------
    namespace : RecursiveNamespace
        Namespace to render
    parent : Tree, optional
        Parent node. DO NOT PASS AN ARGUMENT HERE, by default None
    recursing : bool, optional
        Flag to check if the program is recursing. DO NOT PASS AN ARGUMENT HERE, by default False

    Returns
    -------
    Tree
        Tree to render
    """
    root = (
        parent
        if recursing
        else Tree(":beginner: [bold magenta]Config Root[/bold magenta]")
    )

    for k, v in namespace.__dict__.items():
        node = Tree(f":large_blue_diamond: Node [green]{k!r}[/green]")

        if isinstance(v, RecursiveNamespace):
            root.add(renderTree(v, node, True))
        else:
            node.add(
                f":large_orange_diamond: Value: [italic yellow]{v!r}[/italic yellow]"
            )
            node.add(f":large_orange_diamond: Type: [cyan]{type(v).__name__}[/cyan]")
            root.add(node)

    return root
