def massReplace(target: str, replaces: list[tuple[str, str]]):
    for before, after in replaces:
        target = target.replace(before, after)

    return target


def toPropertyName(prop: str):
    return massReplace(
        prop, [(char, "_") for char in " -!@#$%^&*()_+\{\}\\|;:'\"<,>./?`~"]
    ).lower()
