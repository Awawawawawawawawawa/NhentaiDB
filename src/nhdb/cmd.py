from typing import Callable, Sequence
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich import print


class CommandInterpreter:
    def __init__(self) -> None:
        self.console = Console()
        self.commands: list[dict] = []

    def command(self, alias: str | Sequence[str] = None, force: bool = False):
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
            Force the alias. When forced, the alias becomes the `alias` parameter instead of the function's, by default False
        """

        # This took forever to make ;-;
        def decorator(callback: Callable):
            self.commands.append(
                {
                    "call": callback,
                    "doc": callback.__doc__,
                    "alias": alias or callback.__name__,
                }
            )

            return callback

        return decorator

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
                        "\n".join(
                            map(lambda line: line.strip("\n "), call.__doc__.splitlines())
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

    def promptLoop(self):
        """
        Initiates the Prompt Loop
        """
        while True:
            match Prompt.ask("").split():
                case ["help", *cmd]:
                    self.printHelp(cmd)
                case [func, *args]:
                    if (res := self.searchCommand(func)) is not None:
                        res(*args)

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
        self.promptLoop()
