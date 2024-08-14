import re
import sys

from pathlib import Path
from tap import Tap

from cli_args import BaseTap, RegExArg


def fack():
    class Args(BaseTap):
        root: Path
        dirs_only: bool
        all: bool
        pattern: re.Pattern

        def configure(self) -> None:
            self.description = 'Regex search file system items'
            self.add_root_optional('Directory to search')
            self.add_flag("-d", "--dirs-only", help="Only find directories")
            self.add_flag("-a", "--all", help="Include files and directories")
            self.add_argument("pattern", type=RegExArg, help="Regex pattern")

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
