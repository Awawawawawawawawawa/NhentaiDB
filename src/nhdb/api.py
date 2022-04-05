from nhentei.nfunctions import getByID
from itertools import count
from asyncio import run

from .store import RecursiveNamespace


class SauceDeliverer:
    def __init__(self) -> None:
        """
        Event-Driven Class to deliver sauce
        """
        pass

    def run(self):
        for i in count():
            yield RecursiveNamespace(**run(getByID(i)))
