from dataclasses import dataclass
from pathlib import Path
import os
from typing import List

from utils import pretty_size


@dataclass
class Dir:
    name: str
    size: int


def print_dir(d: Dir):
    print(f'{pretty_size(d.size)}\t\t{d.name}')


def main():
    total: int = 0
    root_size: int = 0
    dirs: List[Dir] = []
    root = Path('./').resolve()

    for d in root.iterdir():
        if d.is_dir():
            size: int = 0

            for path, _, files in os.walk(d):
                p = Path(path)
                for f in files:
                    fp = p / f
                    # noinspection PyBroadException
                    try:
                        size += os.path.getsize(fp)
                    except:
                        print(f'Dont\'t have permissions to {fp.relative_to(root).as_posix()}')
                        exit(1)

            total += size
            dirs.append(Dir(d.name, size))
        else:
            root_size += os.path.getsize(d)

    total += root_size

    if root_size > 0:
        dirs.append(Dir('[Root]', root_size))

    dirs = sorted(dirs, key=lambda dd: dd.size, reverse=False)

    for d in dirs:
        print_dir(d)

    print_dir(Dir('[Total]', total))


if __name__ == '__main__':
    main()
