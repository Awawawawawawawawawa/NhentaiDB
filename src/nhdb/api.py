from nhentei.nfunctions import getByID
from itertools import count
from asyncio import run
from retrying import retry

from .store import RecursiveNamespace


def grabSauces(start: int = 1):
    for i in count(start):
        data = grabRawData(i)
        if isinstance(data, dict):
            yield RecursiveNamespace(**data)


@retry
def grabRawData(id: int):
    return run(getByID(id))
