import errno
import traceback
import os
import signal
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from multiprocessing import Pool
from typing import List, Tuple, Iterator, Dict, Self, Union, Any
from prettytable import PrettyTable, PLAIN_COLUMNS

from cli_args import BaseTap

from utils import pretty_size, int_safe, ShellColors
from logger import Logger

_log: Logger


@dataclass
class Dir:
    name: str
    size: int
    file_count: Union[int, None]

    def density(self) -> Union[int, None]:
        if self.file_count is None:
            return None
        elif self.file_count == 0 or self.size == 0:
            return 0

        return round(self.size / self.file_count)


class State:
    _errors: Dict[str, List[Path]]
    root: Path
    dirs: List[Dir]
    total_size: int
    total_file_count: int
    root_size: int
    root_file_count: int

    def __init__(self, root: Path) -> None:
        self._errors = {}
        self.dirs = []
        self.total_size = 0
        self.total_file_count = 0
        self.root_size = 0
        self.root_file_count = 0
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

    def merge(self, state: Self) -> None:
        for k in state._errors.keys():
            for path in state._errors[k]:
                self.error(k, path)

        for d in state.dirs:
            self.dirs.append(d)

        self.total_size += state.total_size
        self.total_file_count += state.total_file_count
        self.root_size += state.root_size
        self.root_file_count += state.root_file_count


class Args(BaseTap):
    root: Path = Path('./')
    threads: int = None
    timed: bool = False
    trace: bool = False
    no_term_colors: bool = False
    exclude_hidden: bool = False
    exclude_folders: List[Path] = []

    def configure(self) -> None:
        self.description = "A beefed up du"
        self.add_root_optional('Path to scan')
        self.add_argument("-th", "--threads", help="Max threads", type=int)
        self.add_flag("-eh", "--exclude-hidden", help="Exclude hidden files and folders")
        self.add_flag("--timed", help="Print seek time")
        self.add_flag("--no-term-colors", help="Disable terminal colors")
        self.add_trace()

    def process_args(self) -> None:
        global _log

        _log = Logger(self.trace, self.trace, disable_log_color=self.no_term_colors)

        if self.threads is None:
            cores = int_safe(os.environ.get('ZSHCOM__cpu_cores'))

            if cores is not None and cores > 2:
                if cores <= 4:
                    self.threads = 2
                else:
                    self.threads = cores - 1
            else:
                self.threads = 1

            if self.threads < 2:
                _log.warn('Running in single-threaded mode')

        # noinspection SpellCheckingInspection
        efpath = Path(Path.home() / '.duh_exclude')

        if efpath.exists():
            with efpath.open() as f:
                for line in f.readlines():
                    if line:
                        lp = Path(line.strip())
                        if lp.is_dir():
                            self.exclude_folders.append(lp.resolve())


_args: Args


def exclude_dir(d: Path, args: Args) -> bool:
    return (args.exclude_hidden and d.name.startswith('.')) or d.resolve() in args.exclude_folders or d.is_mount()


def walk_dir(wdir: Path, state: State, log: Logger, args: Args) -> Iterator[Tuple[Path, List[Path]]]:
    log.trace(f'Walking {wdir.as_posix()}')
    dirs_left: List[Path] = [wdir]

    while len(dirs_left) > 0:
        cd = dirs_left.pop(0)

        try:
            cd_it = list(cd.iterdir())
        except OSError as e:
            if e.errno == errno.EACCES:
                state.error('Permission denied in', cd)
                continue
            else:
                raise e

        log.trace(f'Getting fs {cd.as_posix()}')
        if cd_it:
            files: List[Path] = []

            for fso in cd_it:
                try:
                    if not fso.is_mount() and not fso.is_symlink():
                        if fso.is_dir():
                            if not exclude_dir(fso, args):
                                dirs_left.append(fso)
                            else:
                                state.error('Excluded', fso)
                        elif fso.is_file():
                            files.append(fso)
                except OSError as e:
                    if e.errno == errno.EACCES:
                        state.error('Permission denied in', fso)
                    elif e.errno != errno.ESTALE:
                        raise e

            yield cd, files


def process_root_fso(fso: Path, task_state: State, log: Logger, args: Args) -> State:
    # noinspection PyBroadException
    try:
        log.trace(f'Processing {fso.as_posix()}')
        if fso.is_dir() and not fso.is_symlink():
            size: int = 0
            count: int = 0

            for path, files in walk_dir(fso, task_state, log, args):
                log.trace(f'Scanning   {path.as_posix()}')
                if args.exclude_hidden and path.name.startswith('.'):
                    continue

                for f in files:
                    if args.exclude_hidden and f.name.startswith('.'):
                        continue

                    # noinspection PyBroadException
                    try:
                        size += f.stat().st_size
                        count += 1
                    except:
                        task_state.error('Unable to stat', f)

            task_state.total_size += size
            task_state.total_file_count += count
            task_state.dirs.append(Dir(fso.name, size, count))
        elif fso.is_file():
            if not args.exclude_hidden or not fso.name.startswith('.'):
                # noinspection PyBroadException
                try:
                    task_state.root_size += fso.stat().st_size
                    task_state.root_file_count += 1
                    task_state.total_size += task_state.root_size
                    task_state.total_file_count += 1
                except:
                    task_state.error('Unable to stat', fso)
    except OSError as e:
        if e.errno == errno.EACCES:
            task_state.error('Permission denied in', fso)
        elif e.errno != errno.ESTALE:
            task_state.error(f'OSERROR ({e.errno})', fso)
    except Exception as e:
        task_state.error('Unhandled Exception', fso)

    log.trace(f'Completed  {fso.as_posix()}')
    return task_state


def collect_sizes_parallel(state: State) -> None:
    pool_objs = []

    for d in state.root.iterdir():
        if not exclude_dir(d, _args):
            pool_objs.append((d, State(state.root), _log, _args))
        else:
            state.error('Excluded', d)

    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    with Pool(processes=_args.threads) as pool:
        sigint_fired = False

        def sigint_handler(sig, frame) -> Any:
            # noinspection PyGlobalUndefined
            global sigint_fired

            _log.trace('SIGINT fired')
            sigint_fired = True
            return original_sigint_handler(sig, frame)

        signal.signal(signal.SIGINT, sigint_handler)

        try:
            task = pool.starmap_async(process_root_fso, pool_objs)
            while not task.ready():
                if sigint_fired:
                    _log.trace('Waiting for task')
                continue
            _log.trace("Collecting thread results")
            results: List[State] = task.get()
        except KeyboardInterrupt:
            exit(0)

        for r in results:
            state.merge(r)


def collect_sizes_single(state: State) -> None:
    for d in state.root.iterdir():
        if not exclude_dir(d, _args):
            process_root_fso(d, state, _log, _args)
        else:
            state.error('Excluded', d)


def print_dir(d: Dir):
    print(f'{pretty_size(d.size)}\t\t{d.name}')


def print_grid(dirs: List[Dir]):
    dirs = [[pretty_size(d.size), pretty_size(d.density()), d.name] for d in dirs]
    grid = PrettyTable(['Size', 'Density', 'Folder'])
    grid.add_rows(dirs)
    grid.set_style(PLAIN_COLUMNS)
    grid.border = False
    grid.padding_width = 0
    grid.left_padding_width = 0
    grid.right_padding_width = 2
    grid.align['Size'] = 'r'
    grid.align['Density'] = 'r'
    grid.align['Folder'] = 'l'

    print(grid)


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

        if state.root_size > 0:
            state.dirs.append(Dir('[Root]', state.root_size, state.root_file_count))

        dirs = sorted(state.dirs, key=lambda dd: dd.size, reverse=False)
        dirs.append(Dir('[Total]', state.total_size, state.total_file_count))
        print_grid(dirs)

        if state.any_errors():
            print(ShellColors.FAIL)
            errors = state.get_errors()
            for k in errors:
                print(f'{k}:\n\t{"\n\t".join(errors[k])}{ShellColors.OFF}')

        if _args.timed:
            print(ShellColors.OKGREEN)
            print(f'Seek time: {st.total_seconds()}{ShellColors.OFF}')
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    main()
