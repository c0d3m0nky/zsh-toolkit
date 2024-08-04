import os
from dataclasses import dataclass
from pathlib import Path
import re
import shutil

from tap import Tap

from utils import arg_to_re, arg_to_path


class Args(Tap):
    source: Path
    destination: str
    pattern: re.Pattern
    invert_match: bool
    files_only: bool
    dirs_only: bool
    exclude_hidden: bool
    do_copy: bool
    plan: bool = False

    def configure(self) -> None:
        self.description = 'Move with regular expressions\n'
        self.epilog = r"Example: rxmv -f ./ '!./\1/\2' '^(\d{4})-(\d+).+$'"

        self.add_argument("source", type=arg_to_path, help="Move root")
        self.add_argument("destination", type=str, help="Folder to move to. Prefix with ! for regex replace")
        self.add_argument("pattern", type=arg_to_re, help="Regex filter")
        self.add_argument("-i", "--invert-match", action='store_true', help="Treat pattern as exclude", required=False)
        self.add_argument("-f", "--files-only", action='store_true', help="Files only", required=False)
        self.add_argument("-d", "--dirs-only", action='store_true', help="Folders only", required=False)
        self.add_argument("-eh", "--exclude-hidden", action='store_true', help="Exclude dot files", required=False)
        self.add_argument("-c", "--do-copy", action='store_true', help="Exclude dot files", required=False)
        self.add_argument("-p", "--plan", action='store_true', help="Exclude dot files", required=False)


@dataclass
class Action:
    src: Path
    dest: Path
    mkdir: bool = False


# noinspection PyRedundantParentheses
def find_common_path(src: Path, dest: Path) -> tuple[Path, Path]:
    for dp in dest.parents:
        for sp in src.parents:
            if dp.is_relative_to(sp):
                return (src.relative_to(sp.parent), dest.relative_to(sp.parent))

    return (src, dest)


def main():
    args = Args().parse_args()

    src = args.source
    rx = args.pattern

    actions = []
    mkdirs = []
    do_all = ''

    for p in src.iterdir():
        is_match = bool(rx.search(p.name))

        if (
                (not args.exclude_hidden or not p.name.startswith('.')) and
                (not args.files_only or p.is_file()) and
                (not args.dirs_only or p.is_dir()) and
                ((args.invert_match and not is_match) or (not args.invert_match and is_match))
        ):
            base_renamed = False

            if args.destination.startswith('!'):
                tgt_replace = args.destination[1:]
                base_renamed = not tgt_replace.endswith('/')
                tgt = Path(re.sub(rx, tgt_replace, p.name))
            else:
                tgt = Path(args.destination)

            if tgt.parent.as_posix() == '/':
                print('Cannot target root directory')
                exit(1)

            fp = p.resolve()

            if base_renamed:
                np = tgt.resolve()
            else:
                np = (tgt / p.name).resolve()

            if np.is_relative_to(fp):
                (rfp, rnp) = find_common_path(fp, np)
                print(f'Target is within source: {rfp.as_posix()} <> {rnp.as_posix()}')
                exit(1)

            if np.exists():
                good = False
                skip = False
                while not good:
                    if not do_all:
                        chc = input(f'{np.name} already exists auto number, skip, or cancel (a/s/c): ').lower()

                        if chc.endswith('+'):
                            chc = chc.strip('+')
                            do_all = chc
                    else:
                        chc = do_all

                    if chc == 's':
                        if do_all:
                            print(f'Skipping {np.name}')
                        skip = True
                        break
                    elif chc == 'c':
                        return
                    elif chc == 'a':
                        if do_all:
                            print(f'Auto numbering {np.name}')
                        good = True
                        npa = np
                        i = 1
                        while npa.exists():
                            npa = np.parent / f'{np.stem} ({i}){np.suffix}'
                            i += 1
                        np = npa
                    elif do_all:
                        do_all = ''

                if skip:
                    continue

            np_parent = np if base_renamed and not p.is_file() else np.parent

            if not np_parent.exists() and np_parent.as_posix() not in mkdirs:
                mkdirs.append(np_parent.as_posix())
                actions.append(Action(fp, np_parent, mkdir=True))

            actions.append(Action(fp, np))

    for a in actions:
        if a.mkdir:
            if args.plan:
                (rsrc, rdest) = find_common_path(a.src, a.dest)
                print(f'mkdir {rdest}')
            else:
                a.dest.mkdir(parents=True)
        else:
            if args.plan:
                max_width = os.get_terminal_size().columns
                (rsrc, rdes) = find_common_path(a.src, a.dest)
                npn = rdes.as_posix()
                opr = '+' if args.do_copy else '-'
                msg = f'{rsrc} {opr}> {npn}'
                if len(msg) > max_width:
                    print(f'\n{rsrc}\n↓\n{npn}')
                else:
                    print(msg)
            else:
                if args.do_copy:
                    if a.src.is_file():
                        shutil.copy(a.src.as_posix(), a.dest.as_posix())
                    else:
                        shutil.copytree(a.src.as_posix(), a.dest.as_posix())
                else:
                    a.src.rename(a.dest)


if __name__ == '__main__':
    main()
