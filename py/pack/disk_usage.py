import errno
import os
import shutil
import signal
from datetime import datetime
from pathlib import Path
from multiprocessing import Pool
from typing import List, Tuple, Iterator, Dict, Any, Callable
from prettytable import PrettyTable, PLAIN_COLUMNS

from cli_args import BaseTap

from utils import pretty_size, int_safe, ShellColors, truncate, distinct, human_int
from logger import Logger

from disk_usage_models import Dir, State, Field, Grid, BareStat, Stat


def get_term_cols():
    # return 63
    return shutil.get_terminal_size().columns


_log: Logger
_fields: Dict[str, Callable[[Stat], Any]] = {
    'size': lambda d: d.size,
    'count': lambda d: d.file_count,
    'density': lambda d: d.density,
    'max': lambda d: d.max_size,
}
_field_choices = [f for f in _fields.keys() if f != 'size']


class Args(BaseTap):
    root: Path = Path('./')
    fields: List[str]
    sort: str
    sort_reversed: bool
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
        self.add_flag('-r', '--sort-reversed', help='Reversed sort')
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
_size_field_width = 7
_name_min_width = 17


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


def process_files(files: List[Path], task_state: State, args: Args) -> Tuple[State, List[int]]:
    sizes: List[int] = []

    for f in files:
        if args.exclude_hidden and f.name.startswith('.'):
            continue

        # noinspection PyBroadException
        try:
            sizes.append(f.stat().st_size)
        except:
            task_state.error('Unable to stat', f)

    # noinspection PyRedundantParentheses
    return (task_state, sizes)


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

                (_, s) = process_files(files, task_state, args)
                dr.sizes += s
                dr.had_error(task_state.has_errors)

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


def collect_sizes_parallel(state: State, dirs: List[Path], root_files: List[Path]) -> None:
    pool_objs = [(d, state.task_state(d), _log, _args) for d in dirs]
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
            task2 = pool.starmap_async(process_files, [(root_files, state.task_state(state.root), _args)])
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

        for (task_state, sizes) in results2:
            for size in sizes:
                task_state.add_to_root(size, task_state.has_errors)
            state.merge(task_state)


def collect_sizes_single(state: State, dirs: List[Path], root_files: List[Path]) -> None:
    for d in dirs:
        state.merge(process_root_fso(d, state.task_state(d), _log, _args))

    (task_state, sizes) = process_files(root_files, state.task_state(state.root), _args)
    for size in sizes:
        task_state.add_to_root(size, task_state.has_errors)
    state.merge(task_state)


def color_field(f: Field, d: Dir, value: str) -> str:
    pref = ''
    suff = ''

    if d.has_errors:
        pref = ShellColors.Yellow
        suff = ShellColors.Off
    elif f.color is not None:
        pref = f.color
        suff = ShellColors.Off

    return f'{pref}{value}{suff}'


def print_grid(grid: Grid, sorted_dirs: List[Stat], total_dir: Stat):
    max_count_len = len(human_int(total_dir.file_count))

    grid.additional_fields['count'].width = max_count_len + grid.int_field_padding

    while grid.remaining_width(grid.field_padding) <= _name_min_width:
        grid.remove_last_field()

    name_max_width = grid.remaining_width() - grid.field_padding
    grid.add_field(Field('Folder', 'l', lambda f, d: color_field(f, d, truncate(d.name, name_max_width, True)), name_max_width))

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


def prep_grid(max_name_len: int) -> Grid:
    grid = Grid(get_term_cols(), max_name_len)
    grid.add_field(Field('Size', 'r', lambda f, d: color_field(f, d, pretty_size(d.size)), _size_field_width))

    # The order determines priority of auto adding
    grid.additional_fields = {
        'density': Field('Density', 'r', lambda f, d: color_field(f, d, pretty_size(d.density)), _size_field_width + grid.int_field_padding, ShellColors.Cyan),
        'count': Field('Count', 'r', lambda f, d: color_field(f, d, human_int(d.file_count)), _size_field_width + grid.int_field_padding),
        'max': Field('Max', 'r', lambda f, d: color_field(f, d, pretty_size(d.max_size)), _size_field_width + grid.int_field_padding)
    }

    if _args.sort and _args.sort != 'size':
        fld = grid.additional_fields[_args.sort]
        fld.color = ShellColors.Green
        grid.add_field(fld)

    if grid.remaining_width(grid.field_padding) <= _name_min_width:
        print('Terminal too narrow')
        exit(1)

    if _args.fields:
        for fld in _args.fields:
            if fld in grid.additional_fields:
                grid.add_field(grid.additional_fields[fld])
    else:
        if max_name_len > 32:
            name_allocation = 32
        else:
            name_allocation = max_name_len

        for fld in grid.additional_fields.values():
            if grid.can_fit_field(fld, name_allocation):
                grid.add_field(fld)

    return grid


def main():
    global _args

    try:
        _args = Args().parse_args()
        state = State(_args.root.resolve(), BareStat('./'), BareStat('Total'))

        sorter: Callable[[Stat], Any]

        if _args.sort in _fields:
            sorter = _fields[_args.sort]
        else:
            print(f'Invalid sort argument {_args.sort}')
            exit(1)

        st = datetime.now()

        max_name_len = 0
        root_dirs: List[Path] = []
        root_files: List[Path] = []

        for fso in _args.root.iterdir():
            if fso.is_dir():
                if not exclude_dir(fso, _args):
                    root_dirs.append(fso)
                    name_len = len(fso.name)
                    if name_len > max_name_len:
                        max_name_len = name_len
                else:
                    # ToDo: Make warning/log
                    state.error('Excluded', fso)
            elif fso.is_file():
                root_files.append(fso)

        grid = prep_grid(max_name_len)

        if _args.threads == 1:
            collect_sizes_single(state, root_dirs, root_files)
        elif _args.threads > 1:
            collect_sizes_parallel(state, root_dirs, root_files)
        else:
            _log.error('Threads must be 1 or greater.')
            exit(1)
        st = datetime.now() - st

        if state.root_stat.size > 0:
            state.add_dir(state.root_stat)

        sorted_dirs = sorted(state.dirs, key=sorter, reverse=_args.sort_reversed)
        print_grid(grid, sorted_dirs, state.total_stat)

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
