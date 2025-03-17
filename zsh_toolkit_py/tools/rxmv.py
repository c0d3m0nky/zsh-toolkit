import os
from dataclasses import dataclass
from pathlib import Path
import re
import shutil

from zsh_toolkit_py.shared.cli_args import BaseTap, RegExArg


class Args(BaseTap):
    root: Path
    destination: str
    pattern: re.Pattern
    invert_match: bool
    files_only: bool
    dirs_only: bool
    exclude_hidden: bool
    do_copy: bool
    plan: bool = False

    def configure(self) -> None:
        self.description = 'Move with regular expressions'
        self.epilog = r"Example: rxmv -f ./ '!./\1/\2' '^(\d{4})-(\d+).+$'"

        self.add_root('Move root')
        self.add_argument('destination', help='Folder to move to. Prefix with ! for regex replace')
        self.add_argument('pattern', type=RegExArg, help='Regex filter')
        self.add_flag('-i', '--invert-match', help='Treat pattern as exclude')
        self.add_flag('-f', '--files-only', help='Files only')
        self.add_flag('-d', '--dirs-only', help='Folders only')
        self.add_flag('-eh', '--exclude-hidden', help='Exclude dot files')
        self.add_flag('-c', '--do-copy', help='Exclude dot files')
        self.add_plan("Don't commit moves")


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

    src = args.root

    if not src.exists():
        return

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

            fp = p.expanduser().resolve()

            if base_renamed:
                np = tgt.expanduser().resolve()
            else:
                np = (tgt / p.name).expanduser().resolve()

            if np == fp:
                continue

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
                (rel_src, rel_dest) = find_common_path(a.src, a.dest)
                print(f'mkdir {rel_dest}')
            else:
                a.dest.mkdir(parents=True)
        else:
            if args.plan:
                max_width = os.get_terminal_size().columns
                (rel_src, rel_dest) = find_common_path(a.src, a.dest)
                npn = rel_dest.as_posix()
                opr = '+' if args.do_copy else '-'
                msg = f'{rel_src} {opr}> {npn}'
                if len(msg) > max_width:
                    print(f'\n{rel_src}\n↓\n{npn}')
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
