import errno
import os
import signal
from datetime import datetime
from pathlib import Path
from multiprocessing import Pool
from typing import List, Tuple, Iterator, Dict, Any, Callable
from prettytable import PrettyTable, PLAIN_COLUMNS

from cli_args import BaseTap

from utils import pretty_size, int_safe, ShellColors, truncate, distinct, human_int
from logger import Logger

from disk_usage_models import Dir, State, Field, Grid

_log: Logger
_fields: Dict[str, Callable[[Dir], Any]] = {
    'size': lambda d: d.size,
    'count': lambda d: d.file_count,
    'density': lambda d: d.density,
}
_field_choices = [f for f in _fields.keys() if f != 'size']


class Args(BaseTap):
    root: Path = Path('./')
    fields: List[str]
    sort: str
    threads: int = None
    timed: bool = False
    trace: bool = False
    no_term_colors: bool = False
    exclude_hidden: bool = False
    exclude_folders: List[Path] = []

    def configure(self) -> None:
        self.description = "A beefed up du"
        self.add_root_optional('Path to scan')
        self.add_multi('-f', '--fields', help="Fields to output", choices=_field_choices, default=None)
        self.add_optional('-s', '--sort', help='Sort by field', choices=list(_fields.keys()), default='size')
        self.add_argument("-th", "--threads", help="Max threads", type=int)
        self.add_flag("-eh", "--exclude-hidden", help="Exclude hidden files and folders")
        self.add_flag("--timed", help="Print seek time")
        self.add_flag("--no-term-colors", help="Disable terminal colors")
        self.add_trace()

    def process_args(self) -> None:
        global _log

        _log = Logger(self.trace, self.trace, disable_log_color=self.no_term_colors)

        if self.fields:
            self.fields = distinct(self.fields)

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
    return (args.exclude_hidden and d.name.startswith('.')) or d.resolve() in args.exclude_folders or d.is_mount() or d.is_symlink()


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


def process_files(files: List[Path], task_state: State, args: Args) -> Tuple[State, int, int]:
    size: int = 0
    count: int = 0

    for f in files:
        if args.exclude_hidden and f.name.startswith('.'):
            continue

        # noinspection PyBroadException
        try:
            size += f.stat().st_size
            count += 1
        except:
            task_state.error('Unable to stat', f)

    # noinspection PyRedundantParentheses
    return (task_state, size, count)


def process_root_fso(fso: Path, task_state: State, log: Logger, args: Args) -> State:
    # noinspection PyBroadException
    try:
        log.trace(f'Processing {fso.as_posix()}')
        if fso.is_dir() and not exclude_dir(fso, args):
            dr = Dir(fso.name)

            for path, files in walk_dir(fso, task_state, log, args):
                log.trace(f'Scanning   {path.as_posix()}')
                if args.exclude_hidden and path.name.startswith('.'):
                    continue

                (_, s, c) = process_files(files, task_state, args)
                dr.size += s
                dr.file_count += c
                dr.has_errors = dr.has_errors or task_state.has_errors

            task_state.add_dir(dr)
        elif fso.is_file():
            task_state.error('process_root_fso is file', fso)
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
    root_files: List[Path] = []

    for d in state.root.iterdir():
        if d.is_dir():
            if not exclude_dir(d, _args):
                pool_objs.append((d, State(state.root), _log, _args))
            else:
                # ToDo: Make warning/log
                state.error('Excluded', d)
        elif d.is_file():
            root_files.append(d)

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
            task2 = pool.starmap_async(process_files, [(root_files, State(state.root), _args)])
            while not task.ready():
                if sigint_fired:
                    _log.trace('Waiting for walk task')
                continue
            while not task2.ready():
                if sigint_fired:
                    _log.trace('Waiting for root files task')
                continue
            _log.trace("Collecting thread results")
            results: List[State] = task.get()
            results2: List[State] = task2.get()
        except KeyboardInterrupt:
            exit(0)

        for r in results:
            state.merge(r)

        for (task_state, size, count) in results2:
            task_state.add_to_root(size, count, task_state.has_errors)
            state.merge(task_state)


def collect_sizes_single(state: State) -> None:
    root_files: List[Path] = []

    for d in state.root.iterdir():
        if d.is_dir():
            if not exclude_dir(d, _args):
                state.merge(process_root_fso(d, State(state.root), _log, _args))
            else:
                state.error('Excluded', d)
        elif d.is_file():
            root_files.append(d)

    (task_state, size, count) = process_files(root_files, State(state.root), _args)
    task_state.add_to_root(size, count, task_state.has_errors)
    state.merge(task_state)


def print_grid(sorted_dirs: List[Dir], total_dir: Dir):
    # ToDo: Refactor to calculate this before scan and break if can't fit
    size_field_width = 7
    name_min_width = 17
    cols = os.get_terminal_size().columns

    def color(f: Field, d: Dir, value: str) -> str:
        pref = ''
        suff = ''

        if d.has_errors:
            pref = ShellColors.Yellow
            suff = ShellColors.Off
        elif f.color is not None:
            pref = f.color
            suff = ShellColors.Off

        return f'{pref}{value}{suff}'

    max_count_len = len(human_int(total_dir.file_count))
    max_name_len = len(total_dir.name)

    for dr in sorted_dirs:
        dir_len = len(dr.name)
        if dir_len > max_count_len:
            max_count_len = dir_len

    grid = Grid(cols)
    grid.add_field(Field('Size', 'r', lambda f, d: color(f, d, pretty_size(d.size)), size_field_width))

    # The order determines priority of auto adding
    additional_fields: Dict[str, Field] = {
        'density': Field('Density', 'r', lambda f, d: color(f, d, pretty_size(d.density)), size_field_width, ShellColors.Cyan),
        'count': Field('Count', 'r', lambda f, d: color(f, d, human_int(d.file_count)), max_count_len + grid.int_field_padding)
    }

    if _args.sort and _args.sort != 'size':
        fld = additional_fields[_args.sort]
        fld.color = ShellColors.Green
        grid.add_field(fld)

    if _args.fields:
        for fld in _args.fields:
            if fld in additional_fields:
                grid.add_field(additional_fields[fld])

        if grid.remaining_width(grid.field_padding) <= name_min_width:
            print('Terminal too narrow')
            exit(1)
    else:
        if grid.remaining_width(grid.field_padding) <= name_min_width:
            print('Terminal too narrow')
            exit(1)

        if max_name_len > 32:
            name_allocation = 32
        else:
            name_allocation = max_name_len

        for fld in additional_fields.values():
            if grid.can_fit_field(fld, name_allocation):
                grid.add_field(fld)

    name_max_width = grid.remaining_width() - grid.field_padding
    grid.add_field(Field('Folder', 'l', lambda f, d: color(f, d, truncate(d.name, name_max_width, True)), name_max_width))

    dirs = [[f.get_value(f, d) for f in grid.fields] for d in sorted_dirs]
    dirs.append([f'{ShellColors.Bold}{f.get_value(f, total_dir)}{ShellColors.Off}' for f in grid.fields])

    pt = PrettyTable([f.name for f in grid.fields])
    pt.set_style(PLAIN_COLUMNS)
    pt.border = False
    pt.padding_width = 0
    pt.left_padding_width = grid.field_left_padding_width
    pt.right_padding_width = grid.field_right_padding_width
    pt.add_rows(dirs)

    for fld in grid.fields:
        pt.align[fld.name] = fld.alignment

    print(pt)


def main():
    global _args

    if os.get_terminal_size().columns < 60:
        print('Terminal too narrow')
        exit(1)

    try:
        _args = Args().parse_args()
        state = State(_args.root.resolve())

        sorter: Callable[[Dir], Any]

        if _args.sort in _fields:
            sorter = _fields[_args.sort]
        else:
            print(f'Invalid sort argument {_args.sort}')
            exit(1)

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
            state.add_dir(Dir('./', state.root_size, state.root_file_count, state.root_has_errors))

        sorted_dirs = sorted(state.dirs, key=sorter, reverse=False)
        print_grid(sorted_dirs, Dir('Total', state.total_size, state.total_file_count, False))

        if state.has_errors:
            print('')
            errors = state.get_errors()
            for k in errors:
                print(f'{ShellColors.Red}{k}:{ShellColors.Off}\n\t{"\n\t".join(errors[k])}')

        if _args.timed:
            print(ShellColors.Green)
            print(f'Seek time: {st.total_seconds()}{ShellColors.Off}')
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    main()
