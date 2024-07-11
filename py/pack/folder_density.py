import os
import re
import json
from pathlib import Path

from tqdm import tqdm
from tap import Tap
from typing import Dict, Pattern, Callable, List, Union

pprint = lambda s: print(json.dumps(s, indent=2, sort_keys=True))


def arg_to_re(pattern: str) -> re.Pattern:
    return re.compile(pattern)


def arg_to_path(path: str) -> Path:
    return Path(path)


class Args(Tap):
    directory: Path
    file_filter: re.Pattern
    directory_filter: re.Pattern
    path_filter: re.Pattern
    glob: str
    verbose: bool
    sort: bool
    summary: bool
    no_progress: bool
    csv: bool

    def configure(self) -> None:
        self.description = "Print folder size densities"
        self.add_argument('directory', nargs='?', type=arg_to_path, default='./', help="Directory to scan")
        self.add_argument("-f", "--file-filter", type=re.Pattern, default=None, help="Regular expression to match on file name")
        self.add_argument("-d", "--directory-filter", type=re.Pattern, default=None, help="Regular expression to match on directory name")
        self.add_argument("-p", "--path-filter", type=re.Pattern, default=None, help="Regular expression to match on file path")
        self.add_argument("--glob", type=str, default=None, help="Glob to use for search")
        self.add_argument("-v", "--verbose", action='store_true', default=False, help="scan for files containing links to download")
        self.add_argument("-s", "--sort", action='store_true', default=False, help="sort by max file size")
        self.add_argument("-sum", "--summary", action='store_true', default=False, help="Prints single line summarizing all children")
        self.add_argument("-np", "--no-progress", action='store_true', default=False, help="Doesn't report progress")
        self.add_argument("-csv", "--csv", action='store_true', default=False, help="Prints CSV compatible")


_args: Args


def pretty_size(size):
    if size <= 0:
        return '0'
    num = size
    pretty = None
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            pretty = f"{num:3.1f}{unit}B"
            break
        num /= 1024.0

    if not pretty:
        pretty = f"{num:.1f}YiB"

    return pretty


class FileSize:
    size: int
    pretty: str

    def __init__(self, size: int):
        self.size = size
        self.pretty = pretty_size(size)

    def __str__(self):
        return self.pretty


class Result:
    max: int
    files: Union[List[FileSize], FileSize]

    def __init__(self, max_size: int = 0, files: Union[List[FileSize], FileSize] = None):
        self.max = max_size
        self.files = [] if files is None else files


def avg_sizes(files: List[FileSize]) -> FileSize:
    if len(files) == 0:
        return FileSize(0)

    s = 0

    for f in files:
        s += f.size

    return FileSize(int(round(s / len(files), 0)))


def time_convert(sec):
    mins = sec // 60
    sec = sec % 60
    mins = mins % 60
    return f'{int(mins)}:{round(sec, 2):02}'


def count_files(path):
    total = 0
    for subdir, dirs, files in os.walk(path):
        total += len(files)

    return total


def get_densities(root: Path,
                  glob: str = "*",
                  file_filter: Pattern[str] = None,
                  directory_filter: Pattern[str] = None,
                  path_filter: Pattern[str] = None,
                  ignore_file: Path = None,
                  logger: Callable[[str], None] = None,
                  progress: bool = False) -> Union[Dict[str, Result], Result]:
    if not root.is_dir():
        raise Exception(f'{root.as_posix()} is not a directory or does not exist')

    def log(m):
        if logger:
            logger(m)

    def include_file(pp: Path) -> bool:
        # check dir exclude set
        if file_filter:
            return True if file_filter.match(pp.name) else False
        elif path_filter:
            return True if path_filter.match(str(pp)) else False

        return True

    def include_dir(pp: Path) -> bool:
        # check dir exclude set
        if directory_filter:
            # add to set to exclude children
            return True if directory_filter.match(pp.name) else False
        elif path_filter:
            # add to set to exclude children
            return True if path_filter.match(str(pp)) else False

        return True

    def append_size(r: Result, s: FileSize):
        if s and r.max < s.size:
            r.max = s.size
        r.files.append(s)

    res: Dict[str, Result] = {"_": Result()}

    total = count_files(root.as_posix())

    i = 0

    prog = None if not progress else tqdm(total=total, unit_scale=True, unit='F', leave=False, desc=root.name)

    for rp in root.glob(glob or '*'):
        if rp.is_file():
            if include_file(rp):
                append_size(res['_'], FileSize(rp.stat().st_size))
        else:
            if include_dir(rp):
                log(f'Scanning: {rp.name}')
                rpa = Result()
                res[rp.name] = rpa
                for p in rp.rglob(glob or '*'):
                    if p.is_file():
                        if include_file(p):
                            append_size(rpa, FileSize(p.stat().st_size))
                    else:
                        # this is purely to exclude child files if necessary
                        include_dir(p)
                log(f'Completed: {rp.name}')
        i += 1
        if progress:
            prog.update(i)

    if progress:
        prog.close()

    if _args.summary:
        files = []
        fmax = 0

        for k in res:
            files += res[k].files
            if fmax < res[k].max:
                fmax = res[k].max

        return Result(fmax, avg_sizes(files))
    else:
        for k in res:
            res[k].files = avg_sizes(res[k].files)

        return res


# compile regex if provided
def _rec(s):
    return None if s is None else re.compile(s)


def main():
    global _args

    _args = Args().parse_args()
    _res = get_densities(
        Path(_args.directory),
        _args.glob,
        _rec(_args.file_filter),
        _rec(_args.directory_filter),
        _rec(_args.path_filter),
        None,
        lambda m: print(m) if _args.verbose else None,
        not _args.no_progress
    )

    # print(_res)

    def output(desc, density, mx):
        if _args.csv:
            print(f'"{desc}","{density}","{mx}"')
        else:
            print(f'{desc} - {density} | {mx}')

    if not _args.summary:
        sortkey = lambda t: t[1].size

        if _args.sort:
            sortkey = lambda t: t[2]

        for r in sorted(map(lambda k: (k, _res[k].files, _res[k].max), _res), key=sortkey, reverse=False):
            output(r[0], r[1], pretty_size(r[2]))
    else:
        # print(_res)
        # r = _res[_args.directory]
        output(_args.directory, _res["files"], pretty_size(_res.max))


if __name__ == '__main__':
    main()
