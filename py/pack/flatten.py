import re
import sys
import os
import argparse
import subprocess
from pathlib import Path

from tap import Tap
import rclone
from userinput import userinput
import emoji

from typing import List, Callable, Tuple, TypeVar, Union


def _sh(cmd: str):
    p = subprocess.Popen(cmd, shell=True)
    p.wait()

T = TypeVar('T')
R = TypeVar('R')

_rx_leading_posix_path: re.Pattern = re.compile(r'^.?/?')
# _working_dir: Path = Path('../../').resolve()

def int_safe(i: str) -> Union[int, None]:
    try:
        return int(i)
    except:
        return None


# region argparse

class RenameParts:
    def __init__(self, file: Path, root: Path, parts: List[str], extension: str, delimiter: str):
        self.file: Path = file
        self.root: Path = root
        self._orig_parts: List[str] = parts
        self.parts = list(self._orig_parts)
        self.extension: str = extension
        self.delimiter: str = delimiter

    def get_path_str(self):
        return self.delimiter.join(self.parts) + self.extension

    def get_byte_length(self) -> int:
        return len(self.get_path_str().encode('utf-8'))

    def revert_changes(self):
        self.parts = list(self._orig_parts)


class PathPartsRename:
    _cb_replace: Callable[[Path, Path], RenameParts]
    _search_pattern: re.Pattern
    _replace_string: str
    _delimiter: str

    def __init__(self, option: str, delimiter, search_pattern: Union[re.Pattern, None]):
        self._delimiter = delimiter
        self._search_pattern = search_pattern

        if not option:
            self._cb_replace = self._default_replace
            return

        if option.startswith('/') and option.endswith('/'):
            self._cb_replace = self._re_replace

            patt = ''
            repl = ''
            step = 0

            for i in range(1, len(option) - 1):
                if step == 0:
                    if option[i] == '\\' and option[i + 1] == '/':
                        patt += '/'
                        i += 1
                    elif option[i] == '/':
                        step = 1
                else:
                    if option[i] == '\\' and option[i + 1] == '/':
                        repl += '/'
                        i += 1
                    elif option[i] == '/':
                        break

    def replace(self, file: Path, root: Path) -> RenameParts:
        return self._cb_replace(file, root)

    def _default_replace(self, file: Path, root: Path) -> RenameParts:
        parents = [prt.name for prt in file.relative_to(root).parents if prt.name]
        parents.reverse()

        return RenameParts(file, root, parents + [file.stem], file.suffix, self._delimiter)

    def _re_replace(self, file: Path, root: Path) -> RenameParts:
        pos_path = re.sub(_rx_leading_posix_path, '', file.relative_to(root).as_posix())

        res = Path(re.sub(self._search_pattern, self._replace_string, pos_path))
        return RenameParts(file, root, [res.stem], res.suffix, '')


def arg_to_re(pattern: str) -> re.Pattern:
    return re.compile(pattern)


def arg_to_path(path: str) -> Path:
    return Path(path)


class Args(Tap):
    root: Path
    delimiter: str = '_'
    extensions: List[str] = None
    extensions_inverted: List[str] = None
    path_filter: re.Pattern
    file_filter: re.Pattern
    file_rename: PathPartsRename
    plan: bool = False
    keep_empty_dirs = False
    sorter: Callable[[List[T], Callable[[T], R], bool], List[T]] = None

    def configure(self) -> None:
        self.description = 'Flatten directory tree'
        self.add_argument('root', type=arg_to_path, help='Directory path to flatten')
        self.add_argument("-d", "--delimiter", help="Path part delimiter")
        self.add_argument("-p", "--plan", action='store_true', help="Don't commit moves")
        self.add_argument("-e", "--extensions", nargs='+', help="Only include these extensions", required=False)
        self.add_argument("-ei", "--extensions-inverted", nargs='+', help="Exclude these extensions", required=False)
        self.add_argument("-pf", "--path-filter", type=arg_to_re, default='.+',
                          help="Regular expression filter on full path (relative path string is provided without leading . or /)")
        self.add_argument("-ff", "--file-filter", type=arg_to_re, default='.+', help="Regular expression filter on file name")
        self.add_argument("-fr", "--file-rename", type=str, default='', help="Regular expression rename on file (relative path string is provided without leading . or /)")
        self.add_argument("--keep-empty-dirs", type=bool, help="Keep empty dirs", required=False)
        self.add_argument("-s", "--sorter", help=argparse.SUPPRESS)

    def process_args(self) -> None:
        if not self.delimiter == '_' and self.file_rename:
            raise ValueError('Conflicting arguments: --delimiter --file-rename')

        if not self.delimiter and not self.file_rename:
            self.delimiter = '_'

        self.file_rename: str
        self.file_rename = PathPartsRename(self.file_rename, self.delimiter, None)

    def error(self, message):
        print('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


# endregion

_args: Args

_skipped_extensions = {}
_skipped_re_filter = 0


def flatten_path():
    root = _args.root.expanduser().resolve()
    files = _flatten_path(root, root, 0)

    parents: List[str]
    f: Path

    for (parents, f) in files:
        nfn = _args.file_rename.replace(f, root)
        skip_file = False

        def check_file_name():
            global skip_file
            altered = False

            while nfn.get_byte_length() > 254:
                altered = True
                pc = len(nfn.parts)
                print(f'File name too long: {nfn.get_path_str()}')

                print('\nTrim')
                for i in range(0, pc):
                    print(f'\t{i + 1}: {nfn.parts[i]}')

                print('\nReplace')
                for i in range(0, pc):
                    print(f'\t{i + 1 + pc}: {nfn.parts[i]}')

                print('')
                strip_dbyte_act = (pc * 2) + 1
                print(f'\t{strip_dbyte_act}: remove double byte chars')
                strip_emoji_act = (pc * 2) + 2
                print(f'\t{strip_dbyte_act}: remove emoji chars')
                print('')
                skip_act = (pc * 2) + 3
                print(f'\t{skip_act}: skip')
                cancel_act = (pc * 2) + 4
                print(f'\t{cancel_act}: cancel')

                print('\nChoose Action: ')
                act = userinput('Choose Action: ', validator='integer')
                # act = input('')
                act = int_safe(act)

                if act <= pc:
                    pi = act - 1

                    while nfn.get_byte_length() > 255:
                        nfn.parts[pi] = nfn.parts[pi][:-1]
                elif pc < act <= pc * 2:
                    pi = act - 1 - pc
                    repl = userinput(f'Replace with (~ to cancel input): {nfn.parts[pi]}\n')

                    if repl.strip() != '~':
                        nfn.parts[pi] = repl
                elif act == strip_dbyte_act or act == strip_emoji_act:
                    strip_all = act == strip_dbyte_act
                    for i in range(0, len(nfn.parts)):
                        p = nfn.parts[i]
                        np = ''
                        for c in p:
                            if strip_all:
                                if len(c.encode('utf-8')) == 1:
                                    np += c
                            else:
                                if not emoji.is_emoji(c):
                                    np += c

                        nfn.parts[i] = np
                elif act == skip_act:
                    skip_file = True
                    return False
                elif act == cancel_act:
                    exit()
                else:
                    print(f'invalid option')

            return altered

        while check_file_name():
            print(f'New file name: {nfn.get_path_str()}')
            res = userinput('Enter to accept, r to retry, s to skip, c to cancel: ').strip()

            if res == 's':
                skip_file = True
            elif res == 'c':
                exit()
            elif res == 'r':
                nfn.revert_changes()
            else:
                print('accepted')
                break

        if skip_file:
            print('skipping file')

        # exit()

        nfp = root / nfn.get_path_str()
        rel = f.relative_to(root)
        nrel = nfp.relative_to(root)
        wdrel_nfp = nfp.relative_to(root)
        wdrel_f = f.relative_to(root)

        print(f'{rel.as_posix()}\n{nrel.as_posix()}\n')
        if os.path.exists(wdrel_nfp.as_posix()):
            print(f'Target file already exists: {nrel}')
        else:
            if not _args.plan:
                os.rename(wdrel_f.as_posix(), wdrel_nfp.as_posix())

    if not _args.plan:
        rclone.with_config("").run_cmd(command="rmdirs", extra_args=[root.as_posix()])

    if _skipped_extensions:
        exts = '\n'.join(_skipped_extensions.keys())
        print(f'Skipped files with extensions:\n{exts}\n')

    return f'Completed {_args.root.as_posix()}'


def _sort(collection: List[T], key: Callable[[T], R] = None, reverse: bool = False) -> List[T]:
    if _args.sorter:
        return _args.sorter(collection, key, reverse)
    elif key:
        return sorted(collection, key=key, reverse=reverse)
    else:
        return sorted(collection, reverse=reverse)


def _flatten_path(root: Path, target: Path, depth: int) -> List[Tuple[List[str], Path]]:
    files: List[Tuple[List[str], Path]] = []
    coll: List[Path] = _sort([pp for pp in target.iterdir()], lambda x: x.name, True)

    for p in coll:
        if p.is_file():
            if depth == 0:
                continue

            if _flatten_file(p, root):
                rel = p.relative_to(root)
                parents = [prt.name for prt in rel.parents if prt.name]
                parents.reverse()
                files.append((parents, p))
        else:
            files = files + _flatten_path(root, p, depth + 1)

    return files


def _flatten_file(f: Path, root: Path) -> bool:
    global _skipped_re_filter
    suffix = f.suffix.strip('.').lower()

    if (_args.extensions and suffix not in _args.extensions) or (_args.extensions_inverted and suffix in _args.extensions_inverted):
        _skipped_extensions[suffix] = True

        return False

    if _args.file_filter and not _args.file_filter.match(f.name):
        _skipped_re_filter += 1
        return False

    if _args.path_filter and not _args.path_filter.match(re.sub(_rx_leading_posix_path, '', f.relative_to(root).as_posix())):
        _skipped_re_filter += 1
        return False

    return True



def _with_args(args):
    global _args

    # print(f'_with_args: {args}')
    _args = Args().parse_args(args=args)
    res = flatten_path()

    print(res)


def main():
    global _args

    _args = Args().parse_args()
    res = flatten_path()

    print(res)


if __name__ == '__main__':
    main()
