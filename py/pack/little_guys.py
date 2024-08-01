import re
import sys

from pathlib import Path
from tap import Tap

from utils import arg_to_path, arg_to_re


def fack():
    class Args(Tap):
        root: Path
        dirs_only: bool
        all: bool
        pattern: re.Pattern

        def configure(self) -> None:
            self.description = 'Regex search file system items'
            self.add_argument('root', type=arg_to_path, nargs='?', help='Directory to search', default='./')
            self.add_argument("-d", "--dirs-only", action='store_true', default=False, help="Only find directories", required=False)
            self.add_argument("-a", "--all", action='store_true', default=False, help="Include files and directories", required=False)
            self.add_argument("pattern", type=arg_to_re, help="Regex pattern")

    args = Args().parse_args()

    if args.dirs_only and args.all:
        args.dirs_only = False

    for path, dirs, files in args.root.walk():
        p = Path(path)
        if args.all or args.dirs_only:
            for d in dirs:
                if args.pattern.search(d):
                    print((p / d).as_posix())

        if not args.dirs_only:
            for f in files:
                if args.pattern.search(f):
                    print((p / f).as_posix())


if __name__ == '__main__':
    func = sys.argv.pop(1)
    globals()[func]()
