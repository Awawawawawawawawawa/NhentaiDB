from typing import Callable
from nhentei.nfunctions import getByID
from itertools import count
from threading import Thread
from asyncio import run


class SauceDeliverer:
    def __init__(self) -> None:
        """
        Event-Driven Class to deliver sauce
        """
        pass

    def run(self):
        for i in count():
            yield run(getByID(i))
