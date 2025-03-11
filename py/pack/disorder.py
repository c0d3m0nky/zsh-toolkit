import re
import sys
import inspect
from enum import Enum
from typing import List, Dict, Generator, Callable
from random import uniform

from cli_args import BaseTap, RegExArg

_commands: List[str] = []


def _uniform(a: int, b: int) -> int:
    return int(uniform(a, b))


class CommandArgs(BaseTap):
    n: int

    def _add_global_args(self) -> None:
        self.add_argument('n', help='Number of results', type=int)


class Advantage(Enum):
    advantage = 'a'
    disadvantage = 'd'
    none = 'none'


class DieArgs(CommandArgs):
    sides: int
    advantage: Advantage

    def configure(self) -> None:
        self.description = 'Get random words'

        self.add_argument('sides', help='Die sides', type=int)
        super()._add_global_args()
        self.add_argument('-a', '--advantage', help='Advantage (a) or Disadvantage (d)', type=Advantage, choices=[e for e in Advantage], default=Advantage.none, required=False)


def roll_die(n: int, sides: int, advantage: Advantage = Advantage.none) -> Generator[int, None, None]:
    i = 0

    while i < n:
        r = _uniform(1, sides)

        if advantage != Advantage.none:
            ra = _uniform(1, sides)

            if advantage == Advantage.advantage:
                r = max(r, ra)
            else:
                r = min(r, ra)

        i += 1
        yield r


class ForceCase(Enum):
    lower = 'lower'
    upper = 'upper'
    none = 'none'


class WordArgs(CommandArgs):
    case: ForceCase
    alpha: bool
    test: List[re.Pattern]

    def configure(self) -> None:
        self.description = 'Get random words'

        super()._add_global_args()
        self.add_multi('-t', '--test', help='Regex patterns that must match', type=RegExArg, default=[])
        self.add_argument('-c', '--case', help='Force case', type=ForceCase, choices=[e for e in ForceCase], default=ForceCase.none, required=False)
        self.add_flag('-a', '--alpha', help='Strip non-alphanumeric characters')


def generate_words(n: int, tests: List[Callable[[str], bool]], force_case: ForceCase = ForceCase.none, alpha_only: bool = False) -> Generator[str, None, None]:
    from english_words import get_english_words_set

    words: List[str] = list(get_english_words_set(['web2'], lower=(force_case == ForceCase.lower), alpha=alpha_only))
    len_words = len(words)
    drawn: Dict[int, bool] = {}
    i = 0

    while i < n:
        r = _uniform(0, len_words)

        if r not in drawn:
            drawn[r] = True
            asserted = True
            w = words[r]

            if force_case == ForceCase.upper:
                w = w.upper()

            for t in (tests or []):
                if not t(w):
                    asserted = False
                    break

            if asserted:
                i += 1
                yield w


class Args(BaseTap):

    def configure(self) -> None:
        self.description = 'Get randomness'
        self.add_subparsers(dest='cmd')
        self.add_subparser('words', WordArgs)
        self.add_subparser('d', DieArgs)


def _main():
    args: BaseTap = Args().parse_args()

    # noinspection PyUnresolvedReferences
    if args.cmd == 'words':
        # noinspection PyTypeChecker
        args: WordArgs = args

        tests = [(lambda s: bool(t.match(s))) for t in args.test]

        for w in generate_words(args.n, tests, args.case, args.alpha):
            print(w)
    elif args.cmd == 'd':
        # noinspection PyTypeChecker
        args: DieArgs = args

        for w in roll_die(args.n, args.sides, args.advantage):
            print(w)


# noinspection PyRedeclaration
_commands = [name.replace('__cmd_', '').lower() for name, obj in inspect.getmembers(sys.modules[__name__]) if (inspect.isfunction(obj) and name.startswith('__cmd_'))]

if __name__ == '__main__':
    _main()
