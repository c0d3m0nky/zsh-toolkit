from pathlib import Path
import re
import argparse
from typing import Any, Callable, Union, List

from tap import Tap

TypeFunc = Callable[[Any], Any]

RegExPartialBlurb = '(partial patterns will add "^.+" and/or ".+$")'


# noinspection PyPep8Naming
def RegExPartialArg(pattern: str) -> re.Pattern:
    if not pattern.startswith('^'):
        pattern = f'^.+{pattern}'
    if not pattern.endswith('$'):
        pattern = f'{pattern}.+$'

    return re.compile(pattern, re.IGNORECASE)


# noinspection PyPep8Naming
def RegExArg(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


# noinspection PyPep8Naming
def PathArg(path: str) -> Path:
    return Path(path)


# noinspection PyShadowingBuiltins
class BaseTap(Tap):

    def add_root(self, help: str) -> None:
        self.add_argument('root', type=PathArg, help=help)

    def add_root_optional(self, help: str, default: str = './') -> None:
        self.add_argument('root', type=PathArg, nargs='?', help=help, default=default)

    def add_optional(self, *name_or_flags: str, help: str, type: Union[type, Callable[[Any], Any]] = str,
                     choices: List[str] = None, choices_case_insensitive: bool = True,
                     default: Any = None) -> None:
        if choices and choices_case_insensitive:
            type = str.lower
        self.add_argument(*name_or_flags, type=type, help=help, choices=choices, default=default, required=False)

    def add_multi(self, *name_or_flags: str, help: str, type: TypeFunc = str.lower, default: Any = None, required=False) -> None:
        self.add_argument(*name_or_flags, nargs='+', type=type, help=help, default=default, required=required)

    def add_multi_choice(self, *name_or_flags: str, help: str, choices: List[str], default: Any = None) -> None:
        self.add_argument(*name_or_flags, nargs='+', choices=choices, type=str.lower, help=help, default=default, required=False)

    def add_flag(self, *name_or_flags: str, help: str, default: bool = False) -> None:
        self.add_argument(*name_or_flags, action='store_true', help=help, default=default)

    def add_list(self, *name_or_flags: str, help: str, default: Any = None) -> None:
        self.add_argument(*name_or_flags, nargs='+', help=help, default=default, required=False)

    def add_plan(self, help: str) -> None:
        self.add_argument("-p", "--plan", action='store_true', help=help)

    def add_trace(self) -> None:
        self.add_argument('-t', '--trace', action='store_true', help='Trace logging', required=False)

    def add_verbose(self) -> None:
        self.add_argument("-v", "--verbose", action='store_true', default=False, help='Enable verbose logging')

    def add_hidden(self, *name_or_flags: str) -> None:
        self.add_argument(*name_or_flags, help=argparse.SUPPRESS)
