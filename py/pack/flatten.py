import re
import sys
import os
import subprocess
from pathlib import Path

import string_dbyte_utils

if os.environ.get('ZSHCOM__feat_rclone') != 'true':
    print('rclone not installed')
    exit(1)

import rclone
from typing import List, Callable, Tuple, TypeVar, Union

from cli_args import BaseTap, RegExArg
from utils import Ask

_ask = Ask()


def _sh(cmd: str):
    p = subprocess.Popen(cmd, shell=True)
    p.wait()


T = TypeVar('T')
R = TypeVar('R')

_rx_leading_posix_path: re.Pattern = re.compile(r'^.?/?')


def int_safe(i: str) -> Union[int, None]:
    # noinspection PyBroadException
    try:
        return int(i)
    except:
        return None


# region argparse

class RenameParts:
    file: Path
    root: Path
    _orig_parts: List[str]
    parts: List[str]
    extension: str
    delimiter: str

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

    def remove_consecutive_filler_chars(self):
        npa = []
        for p in self.parts:
            npa.append(string_dbyte_utils.remove_consecutive_filler_chars(p))

        self.parts = npa


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


class Args(BaseTap):
    root: Path
    delimiter: str = '_'
    extensions: List[str] = None
    extensions_inverted: List[str] = None
    path_filter: re.Pattern
    file_filter: re.Pattern
    file_rename: PathPartsRename
    replace_dbyte: bool
    plan: bool = False
    keep_empty_dirs = False
    sorter: Callable[[List[T], Callable[[T], R], bool], List[T]] = None

    def configure(self) -> None:
        self.description = 'Flatten directory tree'
        self.add_root('Directory path to flatten')
        self.add_plan("Don't commit moves")
        self.add_optional("-d", "--delimiter", help="Path part delimiter")
        self.add_list("-e", "--extensions", help="Only include these extensions")
        self.add_list("-ei", "--extensions-inverted", help="Exclude these extensions")
        self.add_optional("-pf", "--path-filter", type=RegExArg, default='.+', help="RegEx filter on full path (relative path string is provided without leading . or /)")
        self.add_optional("-ff", "--file-filter", type=RegExArg, default='.+', help="RegEx filter on file name")
        self.add_optional("-fr", "--file-rename", type=str, default='', help="RegEx rename on file (relative path string is provided without leading . or /)")
        self.add_flag('-rdp', "--replace-dbyte", help="Replace double byte chars")
        self.add_flag("--keep-empty-dirs", help="Keep empty dirs")
        self.add_hidden("-s", "--sorter")

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
_max_length = 254


def flatten_path():
    root = _args.root.expanduser().resolve()
    files = _flatten_path(root, root, 0)

    parents: List[str]
    f: Path

    for (parents, f) in files:
        nfn = _args.file_rename.replace(f, root)
        skip_file = False

        def replace_dbyte(keep_emoji: bool):
            for i in range(0, len(nfn.parts)):
                p = nfn.parts[i]
                np = string_dbyte_utils.replace_dbl_byte_chars(p, keep_emoji)

                if np.clean != p:
                    nfn.parts[i] = np.clean

            nfn.remove_consecutive_filler_chars()

        def check_file_name():
            # noinspection PyGlobalUndefined
            global skip_file
            altered = False

            while nfn.get_byte_length() > _max_length:
                altered = True
                option_number = 1
                pc = len(nfn.parts)
                print(f'File name too long: {nfn.get_path_str()}')

                print('\nTrim (will also remove consecutive filler chars in entire string)')
                for i in range(0, pc):
                    print(f'\t{i + 1}: {nfn.parts[i]}')
                    option_number += 1

                print('\nReplace')
                for i in range(0, pc):
                    print(f'\t{i + 1 + pc}: {nfn.parts[i]}')
                    option_number += 1

                if not _args.replace_dbyte:
                    print('')
                    strip_dbyte_act = option_number
                    option_number += 1
                    print(f'\t{strip_dbyte_act}: remove double byte chars and consecutive filler chars')
                    strip_dbyte_keep_emoji_act = option_number
                    option_number += 1
                    print(f'\t{strip_dbyte_keep_emoji_act}: but keep emoji')
                else:
                    strip_dbyte_act = -1
                    strip_dbyte_keep_emoji_act = -2

                print('')
                skip_act = option_number
                option_number += 1
                print(f'\t{skip_act}: skip')
                cancel_act = option_number
                option_number += 1
                print(f'\t{cancel_act}: cancel')

                print('\nChoose Action: ')
                act = _ask.int('Choose Action')

                if act <= pc:
                    # Trim
                    nfn.remove_consecutive_filler_chars()
                    pi = act - 1

                    while nfn.get_byte_length() > _max_length:
                        nfn.parts[pi] = nfn.parts[pi][:-1]
                elif pc < act <= pc * 2:
                    pi = act - 1 - pc
                    repl = _ask.ask(f'Replace with (~ to cancel input): {nfn.parts[pi]}\n')

                    if repl.strip() != '~':
                        nfn.parts[pi] = repl
                elif act == strip_dbyte_act or act == strip_dbyte_keep_emoji_act:
                    replace_dbyte(act == strip_dbyte_keep_emoji_act)
                elif act == skip_act:
                    skip_file = True
                    return False
                elif act == cancel_act:
                    exit()
                else:
                    print(f'invalid option')

            return altered

        if _args.replace_dbyte:
            replace_dbyte(False)

        while check_file_name():
            print(f'New file name: {nfn.get_path_str()}')
            res = _ask.choices('Enter to accept, r to retry, s to skip, c to cancel', choices=['', 's', 'c', 'r'], case_insensitive=True)

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
        n_rel = nfp.relative_to(root)

        print(f'{rel.as_posix()}\n{n_rel.as_posix()}\n')
        if os.path.exists(nfp.as_posix()):
            print(f'Target file already exists: {n_rel}')
        else:
            if not _args.plan:
                os.rename(f.as_posix(), nfp.as_posix())

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
