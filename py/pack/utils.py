from typing import Union


class shellcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    BLACK = '\033[30m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    OFF = '\033[0m'
    NOOP = ''


def parse_bool(s: str) -> Union[bool, None]:
    if s:
        s = s.lower()
        if s in ['yes', 'true', 't', 'y', '1']:
            return True
        elif s in ['no', 'false', 'f', 'n', '0']:
            return False
        else:
            return None
    else:
        return None
