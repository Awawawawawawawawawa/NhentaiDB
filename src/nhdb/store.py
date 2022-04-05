from pathlib import Path
from sqlite3 import connect, Connection
from yaml import load, Loader
from .utils import toPropertyName


class SauceDB:
    def __init__(self, file: Path) -> None:
        self.file = file
        self.connection = connect(file)
        self.database = self.connection.cursor()

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def __enter__(self) -> Connection:
        return self.connection

    def __exit(self, *err):
        del self

class RecursiveNamespace:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, RecursiveNamespace(**v) if isinstance(v, dict) else v)

class ProjectConfig:
    def __init__(self, file: Path) -> None:
        with open(file) as f:
            for name, value in load(f, Loader).items():
                setattr(self, toPropertyName(name), value)
