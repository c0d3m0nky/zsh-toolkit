from typing import Union, List


class ShellColors:
    Blue = '\033[94m'
    Cyan = '\033[96m'
    Green = '\033[92m'
    Yellow = '\033[93m'
    Black = '\033[30m'
    Red = '\033[91m'
    Bold = '\033[1m'
    Underline = '\033[4m'
    Off = '\033[0m'
    Orange = '\033[38;5;12m'
    Indigo = '\033[38;5;92m'
    Violet = '\033[38;5;201m'
    Highlight_Black = '\033[1;40m'
    Highlight_Red = '\033[1;41m'
    Highlight_Green = '\033[1;42m'
    Highlight_Yellow = '\033[1;43m'
    Highlight_Blue = '\033[1;44m'
    Highlight_Magenta = '\033[1;45m'
    Highlight_Cyan = '\033[1;46m'
    Highlight_White = '\033[1;47m'


def int_safe(v) -> Union[int, None]:
    # noinspection PyBroadException
    try:
        return int(v)
    except:
        return None


# noinspection PyDefaultArgument
def parse_bool(s: str, also_true: List[Union[str, None]] = []) -> Union[bool, None]:
    if s is str:
        s = s.lower()
        if s in ['yes', 'true', 't', 'y', '1']:
            return True
        elif s in ['no', 'false', 'f', 'n', '0']:
            return s in also_true
        else:
            return s in also_true

    return s in also_true


def pretty_size(size: int) -> str:
    if size <= 0:
        return '0'
    num = size
    pretty = None
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            pretty = f"{num:3.1f}{unit}B"
            break
        num /= 1024.0

    if not pretty:
        pretty = f"{num:.1f}YiB"

    return pretty
