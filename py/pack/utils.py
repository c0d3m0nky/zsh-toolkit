from typing import Union, List, Any, TypeVar, Callable, Tuple

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


def float_safe(v) -> Union[float, None]:
    # noinspection PyBroadException
    try:
        return float(v)
    except:
        return None


# noinspection PyDefaultArgument
def parse_bool(s: str, also_true: List[Union[str, None]] = []) -> Union[bool, None]:
    if type(s) is str:
        s = s.lower()
        if s in ['yes', 'true', 't', 'y', '1']:
            return True
        elif s in ['no', 'false', 'f', 'n', '0']:
            return False
        else:
            return True if s in also_true else None
    else:
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


def first(coll: List[ZTK_UTV]) -> Union[ZTK_UTV, None]:
    if coll and len(coll) > 0:
        return coll[0]
    else:
        return None


def last(coll: List[ZTK_UTV]) -> Union[ZTK_UTV, None]:
    if coll and len(coll) > 0:
        return coll[len(coll) - 1]
    else:
        return None


def str_in(value: str, coll: List[str], case_insensitive: bool = True, strip: bool = True) -> bool:
    def clean(s: str) -> str:
        if case_insensitive:
            s = s.lower()

        if strip:
            s = s.strip()

        return s

    clean_value = clean(value)

    for ci in coll:
        if clean_value == clean(ci):
            return True

    return False


class Ask:

    def __init__(self):
        pass

    def int(self, msg: str) -> int:
        def mutate(resp: str) -> Tuple[bool, int]:
            resp_int = int_safe(resp)

            # noinspection PyRedundantParentheses
            return (resp_int is not None, resp_int)

        return self._ask(msg, mutate)

    def float(self, msg: str) -> float:
        def mutate(resp: str) -> Tuple[bool, float]:
            resp_float = float_safe(resp)

            # noinspection PyRedundantParentheses
            return (resp_float is not None, resp_float)

        return self._ask(msg, mutate)

    # noinspection PyDefaultArgument
    def yes_no(self, msg: str, empty_is_true: bool = False, also_true: List[Union[str, None]] = []) -> bool:
        if empty_is_true and '' not in also_true:
            also_true.append('')

        def mutate(resp: str) -> Tuple[bool, bool]:
            resp_bool = parse_bool(resp, also_true)

            # noinspection PyRedundantParentheses
            return (resp_bool is not None, resp_bool)

        return self._ask(msg, mutate)

    def char(self, msg: str, also_valid: List[str] = []) -> str:
        def mutate(resp: str) -> Tuple[bool, str]:
            # noinspection PyRedundantParentheses
            return (len(resp) == 1 or str_in(resp, also_valid), resp)

        return self._ask(msg, mutate)

    def choices(self, msg: str, choices: List[str], case_insensitive: bool = False, strip: bool = True) -> str:
        def mutate(resp: str) -> Tuple[bool, str]:
            if case_insensitive:
                resp = resp.lower()

            if strip:
                resp = resp.strip()

            # noinspection PyRedundantParentheses
            return (str_in(resp, choices, case_insensitive, strip), resp)

        return self._ask(msg, mutate)

    def ask(self, msg: str, case_insensitive: bool = False, strip: bool = True, default: Union[str, None] = None) -> str:
        def mutate(resp: str) -> Tuple[bool, str]:
            resp = default if resp is None or resp == '' else resp

            if case_insensitive:
                resp = resp.lower()

            if strip:
                resp = resp.strip()

            # noinspection PyRedundantParentheses
            return (len(resp) > 0, resp)

        return self._ask(msg, mutate)

    # noinspection PyMethodMayBeStatic
    def _ask(self, msg: str, mutate: Callable[[str], Tuple[bool, ZTK_UTV]]) -> ZTK_UTV:
        while True:
            resp = input(f'{msg}: ')
            (is_valid, value) = mutate(resp)

            if is_valid:
                return value
