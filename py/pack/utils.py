from typing import Union, List, Any, TypeVar, Callable

ZTK_UTV = TypeVar('ZTK_UTV')


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


def truncate(s: str, max_len: int, add_ellipse: bool = False) -> str:
    if len(s) > max_len:
        if add_ellipse:
            return s[:max_len - 1] + '…'
        else:
            return s[:max_len]
    else:
        return s


def is_in(obj: ZTK_UTV, seq: List[ZTK_UTV], eq: Callable[[ZTK_UTV, ZTK_UTV], bool]) -> bool:
    for i in seq:
        if eq(i, obj):
            return True

    return False


def distinct(seq: List[ZTK_UTV], eq: Union[Callable[[ZTK_UTV, ZTK_UTV], bool], None] = None) -> List[ZTK_UTV]:
    res: List[ZTK_UTV] = []

    if eq is None:
        for i in seq:
            if i not in res:
                res.append(i)
    else:
        for i in seq:
            if not is_in(i, res, eq):
                res.append(i)

    return res


def pop_n(seq: List[Any], n: int) -> List[Any]:
    res: List[Any] = []

    for i in range(n):
        res.append(seq.pop())

    return list(reversed(res))


def human_int(i: int) -> str:
    sa = list(str(i))
    res = ''

    while len(sa) > 0:
        if len(sa) >= 3:
            rp = ''.join(pop_n(sa, 3))
        else:
            rp = ''.join(pop_n(sa, len(sa)))

        res = f'{rp},{res}' if res else rp

    return res

