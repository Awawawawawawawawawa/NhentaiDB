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

    def printHelp(self, topic):
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
        commands = self.console.input("[magenta]>[/magenta] ").split(";")
        for command in map(lambda c: c.strip(), commands):
            self.handleCommand(command)

    def handleCommand(self, cmd: str):
        match cmd.split():
            case ["help" | "h", *topic]:
                self.printHelp(topic)
            case [function, *args]:
                if (function := self.searchCommand(function)) is None:
                    self.logger.error(f"No such command: [magenta]{function}[/magenta]")
                    self.logger.info(
                        f"Run [yellow bold]help[/yellow bold] to see the list of commands"
                    )
                    return
                functionArgumentTypes = tuple(function.__annotations__.values())

                if (passedArgCount := len(args)) != (
                    functionArgCount := len(functionArgumentTypes)
                ):
                    self.logger.error(
                        f"Expected {functionArgCount} arguments, got {passedArgCount}"
                    )
                    del passedArgCount, functionArgCount
                    return

                argumentsToPass = []
                for index, arg in enumerate(args):
                    target = functionArgumentTypes[index]
                    try:
                        argumentsToPass.append(target(arg))
                    except ValueError:
                        self.logger.error(
                            f"Unable to cast argument {arg!r} to {target.__name__}"
                        )
                        return

                function(*argumentsToPass)

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
