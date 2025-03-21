import re
import sys
from pathlib import Path
from typing import List, Dict, Callable, Any

from zsh_toolkit_py.shared.cli_args import BaseTap, RegExPartialArg, RegExPartialBlurb
from zsh_toolkit_py.shared.file_utils import fs_case_sensitive, CaseSensitiveFileSystemTestResult
from zsh_toolkit_py.shared.utils import int_safe


class Args(BaseTap):
    pattern: re.Pattern
    folder: str
    min_files: int
    plan: bool = False

    def configure(self) -> None:
        self.description = 'Group files into folders'
        self.add_argument('pattern', type=RegExPartialArg, help=f'Regex pattern {RegExPartialBlurb}')
        self.add_argument('folder', help='Group number to use for folder or prefix with ! for substitution')
        self.add_optional('-m', '--min-files', type=int, help='Minimum number of files', default=2)
        self.add_plan("Don't commit moves")


class FileGroup:
    name: str
    files: List[Path]

    def __init__(self, name: str, files: List[str] = None) -> None:
        self.name = name
        self.files = files or []


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

    files: List[Path] = [f for f in root.iterdir() if f.is_file()]
    move_files: Dict[str, FileGroup] = {}

    get_fn: Callable[[re.Match[str], str, Any], str]

    def get_fn_group(match: re.Match[str], name: str, var: Any) -> str:
        return match.group(var)

    def get_fn_sub(match: re.Match[str], name: str, var: Any) -> str:
        return re.sub(args.pattern, var, name)

    get_fn_var: Any
    gn = int_safe(args.folder)

    if gn:
        get_fn_var = gn
        get_fn = get_fn_group
    elif args.folder.startswith('!'):
        get_fn_var = args.folder[1:]
        get_fn = get_fn_sub
    else:
        print('Invalid folder argument', file=sys.stderr)
        exit(1)

    for f in files:
        m = args.pattern.match(f.name)

        if m:
            try:
                fn = get_fn(m, f.name, get_fn_var)
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

                if fnk not in move_files:
                    move_files[fnk] = FileGroup(fn)

                move_files[fnk].files.append(f)

    if args.min_files > 1:
        for k in list(move_files.keys()):
            if len(move_files[k].files) < args.min_files:
                move_files.pop(k, None)

    for mvk in sorted(move_files.keys(), key=lambda sk: sk.lower()):
        g = move_files[mvk]
        print(g.name)
        i = 1

        for f in sorted(g.files, key=lambda sk: sk.name.lower()):
            bracket = '╟' if i < len(files) else '╙'
            print(f'{bracket} {f.name}')
            if not args.plan:
                d = root / g.name

                if not d.exists():
                    d.mkdir()

                nf = d / f.name
                if nf.exists():
                    print('\t  file exists')
                else:
                    f.rename(nf)

            i += 1

        print('')


if __name__ == '__main__':
    main()
