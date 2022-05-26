from typing import Callable, Sequence
from rich.console import Console
from rich.table import Table
from rich import print
from logging import Logger
from textwrap import dedent

from .utils import cleanseArgument


class CommandInterpreter:
    def __init__(self, logger: Logger) -> None:
        self.console = Console()
        self.commands: list[dict] = []
        self.logger = logger
        self.sanityHook = cleanseArgument

    def command(
        self, alias: str | Sequence[str] = None, force: bool = True, hidden: bool = False
    ):
        """
        Adds a function to the object's commands list

        Usage:
        ```py
        @cmd.command()
        def helloWorld():
            print("Hello World!")
        ```

        Parameters
        ----------
        alias : string or a sequence of strings, optional
            Alias/Aliases for the function, by default None
        force : bool, optional
            Force the alias. When forced, the alias becomes the `alias` parameter instead of the function's, by default True
        hidden: bool, optional
            Hide the command from the visible list of commands. This means that the command won't appear when
            the user types in `help` or `h`, by default False
        """

        # This took forever to make ;-;
        def registerCommand(callback: Callable):
            self.commands.append(
                {
                    "call": callback,
                    "doc": callback.__doc__,
                    "alias": alias or callback.__name__,
                    "hidden": hidden,
                }
            )

            return callback

        return registerCommand

    def setSanityHook(self):
        def setSanity(callback: Callable):
            self.sanityHook = callback

            return callback

        return setSanity

    def printHelp(self, topic: str):
        match topic:
            case ["help"]:
                print(
                    """
USAGE: [i]help <topic>[/i]
    Prints the documentation of a command
                """
                )
            case [cmd]:
                if (call := self.searchCommand(cmd)) is not None:
                    print(
                        dedent(
                            "\n".join(
                                map(
                                    lambda line: line.strip("\n"),
                                    call.__doc__.splitlines(),
                                )
                            )
                        )
                    )
                else:
                    self.logger.error(f"No help for {cmd}")
            case [""] | []:
                commands = Table(
                    "Command",
                    "Summary",
                    title="Commands",
                    caption="Run [i]help <command>[/i] to get documentation for that command",
                )

                for command in self.commands:
                    if command.get("hidden"):
                        continue

                    name = command.get("alias")
                    summary = command.get("doc")
                    summary = (
                        summary.strip("\n ").splitlines()[0]
                        if summary is not None
                        else "[red bold]null[/red bold]"
                    )

                    name = ", ".join(name) if isinstance(name, list | tuple) else name

                    commands.add_row(name, summary)

                self.console.print(commands)

    def prompt(self):
        """
        Initiates the Prompt Loop
        """
        commands = self.sanityHook(self.console.input("[magenta]>[/magenta] ")).split(";")

        for command in map(lambda c: c.strip(), commands):
            self.handleCommand(command)

    def handleCommand(self, cmd: str):
        """
        Handles an individual command

        This is usually ran by `prompt` for every command passed in a line

        Parameters
        ----------
        cmd : str
            Command to parse. Should not have any semicolons
        """
        match cmd.split():
            case ["help" | "h", *topic]:  # User asks for help
                self.printHelp(topic)
            case [func, *args]:  # User runs a command
                func, funcExists = self._doesTheCommandExist(func)
                funcCastMap = tuple(func.__annotations__.values())

                if not funcExists:
                    return
                if not self._ensureCorrectArgCount(args, funcCastMap):
                    return

                argumentsToPass = self._castArgs(args, funcCastMap)
                func(*argumentsToPass)

    def _ensureCorrectArgCount(
        self, args: tuple[str], castMap: tuple[dict[str, object]]
    ) -> bool:
        """
        Checks if the arguments can match the cast map 1:1

        Ran by`handleCommand` to check if the correct amount of arguments
        have been passed

        Parameters
        ----------
        args : tuple of strings
            Raw arguments from `prompt`
        castMap : tuple of dictionaries
            The cast map registered by the `command` decorator

        Returns
        -------
        bool
            `True` if all is go, `False` otherwise
        """
        if (passedArgCount := len(args)) != (functionArgCount := len(castMap)):
            self.logger.error(
                f"Expected {functionArgCount} arguments, got {passedArgCount}"
            )
            del passedArgCount, functionArgCount
            return False
        return True

    def _doesTheCommandExist(self, function: str) -> bool:
        """
        Checks if the command exists

        Ran by `handleCommand` in order to check if the command
        even exists in the first place before proceeding

        Parameters
        ----------
        function : str
            Name of the function

        Returns
        -------
        bool
            `True` if all is go, `False` otherwise
        """
        if (function := self.searchCommand(function)) is None:
            self.logger.error(f"No such command: [magenta]{function}[/magenta]")
            self.logger.info(
                f"Run [yellow bold]help[/yellow bold] to see the list of commands"
            )
            return None, False
        return function, True

    def _castArgs(self, args: tuple[str], castMap: tuple[dict[str, object]]) -> list:
        """
        Casts the args according to its map so that the function that will be ran
        can use that object's properties accordingly

        Ran by `handleCommand` in the final step before calling the function

        Parameters
        ----------
        args : tuple of strings
            Raw arguments from `prompt`
        castMap : tuple of dictionaries
            The mapping to reference during casting every argument

        Returns
        -------
        list
            `args` but each object has been casted accordingly
        """
        argumentsToPass = []

        for index, arg in enumerate(args):
            target = castMap[index]
            try:
                argumentsToPass.append(target(arg))
            except ValueError:
                self.logger.error(f"Unable to cast argument {arg!r} to {target.__name__}")
                return
        return argumentsToPass

    def searchCommand(self, alias: str) -> Callable | None:
        return next(
            (
                command.get("call")
                for command in self.commands
                if alias in command.get("alias")
            ),
            None,
        )

    def cmdloop(self):
        while True:
            self.prompt()
