import re
import sys
from pathlib import Path
from typing import List, Dict, Callable, Any

from zsh_toolkit_py.shared.cli_args import BaseTap, RegExPartialArg, RegExPartialBlurb
from zsh_toolkit_py.shared.file_utils import fs_case_sensitive, CaseSensitiveFileSystemTestResult
from zsh_toolkit_py.shared.utils import int_safe


class Args(BaseTap):
    pattern: re.Pattern
    folder_rx_group: str
    dirs: bool
    min_items: int
    plan: bool

    def configure(self) -> None:
        self.description = 'Group files into folders'
        self.add_argument('pattern', type=RegExPartialArg, help=f'Regex pattern {RegExPartialBlurb}')
        self.add_argument('folder_rx_group', help='Group number to use for folder or prefix with ! for substitution')
        self.add_optional('-m', '--min-items', type=int, help='Minimum number of items', default=2)
        self.add_flag('-d', '--dirs', help='Group folders')
        self.add_plan("Don't commit moves")


class Group:
    name: str
    items: List[Path]

    def __init__(self, name: str, items: List[str] = None) -> None:
        self.name = name
        self.items = items or []


def main() -> None:
    args = Args().parse_args()
    root = Path('./').resolve()
    fs_cs = fs_case_sensitive(root)

    if fs_cs == CaseSensitiveFileSystemTestResult.CaseSensitive:
        fs_cs = True
    elif fs_cs == CaseSensitiveFileSystemTestResult.CaseInsensitive:
        fs_cs = False
    else:
        print(f'Case sensitive filesystem check failed: {fs_cs}', file=sys.stderr)
        exit(1)

    if args.dirs:
        items: List[Path] = [f for f in root.iterdir() if f.is_dir()]
    else:
        items: List[Path] = [f for f in root.iterdir() if f.is_file()]

    move_items: Dict[str, Group] = {}

    get_fn: Callable[[re.Match[str], str, Any], str]

    def get_fn_group(match: re.Match[str], name: str, var: Any) -> str:
        return match.group(var)

    def get_fn_sub(match: re.Match[str], name: str, var: Any) -> str:
        return re.sub(args.pattern, var, name)

    get_fn_var: Any
    gn = int_safe(args.folder_rx_group)

    if gn:
        get_fn_var = gn
        get_fn = get_fn_group
    elif args.folder_rx_group.startswith('!'):
        get_fn_var = args.folder_rx_group[1:]
        get_fn = get_fn_sub
    else:
        print('Invalid folder argument', file=sys.stderr)
        exit(1)

    for item in items:
        m = args.pattern.match(item.name)

        if m:
            try:
                fn = get_fn(m, item.name, get_fn_var)
            except IndexError as e:
                if 'no such group' in str(e):
                    print('folder group out of bounds', file=sys.stderr)
                else:
                    print(f'folder name error: {e}', file=sys.stderr)
                exit(1)

            if fn:
                if fs_cs == CaseSensitiveFileSystemTestResult.CaseInsensitive:
                    fnk = fn.lower()
                else:
                    fnk = fn

                if fnk not in move_items:
                    move_items[fnk] = Group(fn)

                move_items[fnk].items.append(item)

    if args.min_items > 1:
        for k in list(move_items.keys()):
            if len(move_items[k].items) < args.min_items:
                move_items.pop(k, None)

    for mvk in sorted(move_items.keys(), key=lambda sk: sk.lower()):
        g = move_items[mvk]
        print(g.name)
        i = 1

        for item in sorted(g.items, key=lambda sk: sk.name.lower()):
            bracket = '╟' if i < len(items) else '╙'
            print(f'{bracket} {item.name}')
            if not args.plan:
                d = root / g.name

                if not d.exists():
                    d.mkdir()

                nf = d / item.name
                if nf.exists():
                    print(f'\t  {"folder" if args.dirs else "file"} exists')
                else:
                    item.rename(nf)

            i += 1

        print('')


if __name__ == '__main__':
    main()
