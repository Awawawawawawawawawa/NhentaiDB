from nhdb import CommandInterpreter

nhdb = CommandInterpreter()


@nhdb.command(["exit", "quit"], True)
def quitApp():
    """
    Quits the program
    """
    exit()


nhdb.cmdloop()
