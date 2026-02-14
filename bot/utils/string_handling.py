import shlex


def split_quotes(text: str) -> list[str]:
    try:
        return list(shlex.split(text))
    except ValueError:
        return text.split(None, 1)
