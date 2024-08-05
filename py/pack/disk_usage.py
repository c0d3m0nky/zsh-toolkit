import errno
import os
import traceback
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from multiprocessing import Pool
from typing import List, Tuple, Iterator, Dict

from tap import Tap

from utils import pretty_size, int_safe, arg_to_path, ShellColors
from logger import Logger

_log: Logger

@dataclass
class Dir:
    name: str
    size: int


class State:
    _errors: Dict[str, List[Path]]
    root: Path
    dirs: List[Dir]
    total: int
    root_size: int

    def __init__(self, root: Path) -> None:
        self._errors = {}
        self.dirs = []
        self.total = 0
        self.root_size = 0
        self.root = root

    def error(self, key: str, path: Path) -> None:
        if key not in self._errors:
            self._errors[key] = []

        self._errors[key].append(path)

    def any_errors(self) -> bool:
        return bool(self._errors.keys())

    def get_relative_path(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def get_errors(self) -> Dict[str, List[str]]:
        return {k: [self.get_relative_path(p) for p in v] for k, v in self._errors.items()}

    # ToDo: When Slackware finally updates to Python 3.10+, use Self
    # noinspection PyProtectedMember
    def merge(self, state) -> None:
        for k in state._errors.keys():
            for path in state._errors[k]:
                self.error(k, path)

        for d in state.dirs:
            self.dirs.append(d)

        self.total += state.total
        self.root_size += state.root_size


class Args(Tap):
    root: Path = Path('./')
    threads: int = None
    timed: bool = False
    trace: bool = False
    exclude_hidden: bool = False
    exclude_folders: List[Path] = []

    def configure(self) -> None:
        self.description = "A beefed up du"
        self.add_argument('root', type=arg_to_path, nargs='?', help='Path to scan')
        self.add_argument("-t", "--threads", type=int, help="Max threads")
        self.add_argument("-eh", "--exclude-hidden", action='store_true', help="Exclude hidden files and folders", default=False)
        self.add_argument("--timed", action='store_true', help="Print seek time")
        self.add_argument("--trace", action='store_true', help="Trace logging")

    def process_args(self) -> None:
        global _log

        _log = Logger(self.trace, False)

        if self.threads is None:
            cores = int_safe(os.environ.get('ZSHCOM__cpu_cores'))

            if cores is not None:
                self.threads = int(cores / 2)
                if self.threads < 1:
                    self.threads = 1
            else:
                self.threads = 1

            if self.threads < 2:
                _log.warn('Running in single-threaded mode')

        efpath = Path(Path.home() / '.duh_exclude')

        if efpath.exists():
            with efpath.open() as f:
                for line in f.readlines():
                    if line:
                        lp = Path(line.strip())
                        if lp.is_dir():
                            self.exclude_folders.append(lp.resolve())


_args: Args


def exclude_dir(d: Path) -> bool:
    return (_args.exclude_hidden and d.name.startswith('.')) or d.resolve() in _args.exclude_folders or d.is_mount()


def print_dir(d: Dir):
    print(f'{pretty_size(d.size)}\t\t{d.name}')


def walk_dir(wdir: Path, state: State) -> Iterator[Tuple[Path, List[Path]]]:
    _log.trace(f'Waling {wdir.as_posix()}')
    dirs_left: List[Path] = [wdir]

    while dirs_left:
        cd = dirs_left.pop(0)

        try:
            cd_it = cd.iterdir()
        except OSError as e:
            if e.errno == errno.EACCES:
                state.error('Permission denied in', cd)
                continue
            else:
                raise e

        _log.trace(f'Scanning {cd.as_posix()}')
        if cd_it:
            files: List[Path] = []

            for fso in cd_it:
                try:
                    if not fso.is_mount() and not fso.is_symlink():
                        if fso.is_dir():
                            if not exclude_dir(fso):
                                dirs_left.append(fso)
                        elif fso.is_file():
                            files.append(fso)
                except OSError as e:
                    if e.errno == errno.EACCES:
                        state.error('Permission denied in', fso)
                    elif e.errno != errno.ESTALE:
                        raise e

            yield cd, files


def process_root_fso(fso: Path, task_state: State) -> State:
    # noinspection PyBroadException
    try:
        if fso.is_dir() and not fso.is_symlink():
            size: int = 0

            for path, files in walk_dir(fso, task_state):
                if _args.exclude_hidden and path.name.startswith('.'):
                    continue

                for f in files:
                    if _args.exclude_hidden and f.name.startswith('.'):
                        continue

                    # noinspection PyBroadException
                    try:
                        size += f.stat().st_size
                    except:
                        task_state.error('Unable to stat', f)

            task_state.total += size
            task_state.dirs.append(Dir(fso.name, size))
        elif fso.is_file():
            if not _args.exclude_hidden or not fso.name.startswith('.'):
                # noinspection PyBroadException
                try:
                    task_state.root_size += fso.stat().st_size
                except:
                    task_state.error('Unable to stat', fso)
    except Exception as e:
        _log.error(f'Exception raised processing "{task_state.get_relative_path(fso)}"', e)
        exit(1)

    return task_state


def collect_sizes_parallel(state: State) -> None:
    pool = Pool(processes=_args.threads)
    pool_objs = [(d, State(state.root)) for d in state.root.iterdir() if not exclude_dir(d)]

    results = pool.starmap(process_root_fso, pool_objs)

    for r in results:
        state.merge(r)


def collect_sizes_single(state: State) -> None:
    for d in state.root.iterdir():
        if not exclude_dir(d):
            process_root_fso(d, state)


def main():
    global _args

    try:
        _args = Args().parse_args()
        state = State(_args.root.resolve())

        st = datetime.now()
        if _args.threads == 1:
            collect_sizes_single(state)
        elif _args.threads > 1:
            collect_sizes_parallel(state)
        else:
            _log.error('Threads must be 1 or greater.')
            exit(1)
        st = datetime.now() - st

        state.total += state.root_size

        if state.root_size > 0:
            state.dirs.append(Dir('[Root]', state.root_size))

        dirs = sorted(state.dirs, key=lambda dd: dd.size, reverse=False)

        for d in dirs:
            print_dir(d)

        print_dir(Dir('[Total]', state.total))

        if state.any_errors():
            print(ShellColors.FAIL)
            errors = state.get_errors()
            delim = "\n\t"
            for k in errors:
                print(f'{k}:\n\t{delim.join(errors[k])}{ShellColors.OFF}')

        if _args.timed:
            print(ShellColors.OKGREEN)
            print(f'Seek time: {st.total_seconds()}{ShellColors.OFF}')
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    main()
