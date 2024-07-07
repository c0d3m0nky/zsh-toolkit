import sys
import os
from pathlib import Path
import re
from argparse import ArgumentParser


def main():
    example = r"Example: rxmv -f ./ '!./\1/\2' '^(\d{4})-(\d+).+$'"
    ap = ArgumentParser(prog='rxmv', epilog=example)
    ap.add_argument("source", type=str, help="Move root")
    ap.add_argument("destination", type=str, help="Folder to move to. Prefix with ! for regex replace")
    ap.add_argument("pattern", type=str, help="Regex filter")
    ap.add_argument("-i", "--invert-match", action='store_true', help="Treat pattern as exclude")
    ap.add_argument("-f", "--files-only", action='store_true', help="Files only")
    ap.add_argument("-d", "--dirs-only", action='store_true', help="Folders only")
    ap.add_argument("-eh", "--exclude-hidden", action='store_true', help="Exclude dot files")
    ap.add_argument("-p", "--plan", action='store_true', help="Exclude dot files")
    args = ap.parse_args(sys.argv)

    src = Path(args.source)
    # tgt = Path(args.destination)
    rx = re.compile(args.pattern, re.I)
    mkdirs = []

    # if tgt.exists() and not tgt.is_dir():
    # 	print('Destination path is existing file')
    # 	return

    for p in src.iterdir():
        is_match = bool(rx.search(p.name))

        if (
                (not args.exclude_hidden or not p.name.startswith('.')) and
                (not args.files_only or p.is_file()) and
                (not args.dirs_only or p.is_dir()) and
                ((args.invert_match and not is_match) or (not args.invert_match and is_match))
        ):
            if args.destination.startswith('!'):
                tgt_replace = args.destination[1:]
                tgt = Path(re.sub(rx, tgt_replace, p.name))
            else:
                tgt = Path(args.destination)

            if tgt.exists() and not tgt.is_dir():
                print(f'Destination path is existing file: {tgt.as_posix()}')
                continue

            np = tgt / p.name

            if not tgt.exists():
                if args.plan:
                    psx = tgt.as_posix()
                    if psx not in mkdirs:
                        mkdirs.append(psx)
                        print(f'mkdir {psx}')
                else:
                    tgt.mkdir(parents=True)

            if np.exists():
                good = False
                skip = False
                while not good:
                    chc = input(f'{np.name} already exists auto number, skip, or cancel (a/s/c): ').lower()
                    if chc == 's':
                        good = True
                        skip = True
                        continue
                    elif chc == 'c':
                        good = True
                        return
                    elif chc == 'a':
                        good = True
                        npa = np
                        i = 1
                        while npa.exists():
                            npa = np.parent / f'{np.stem} ({i}){np.suffix}'
                            i += 1
                        np = npa

            if args.plan:
                max_width = os.get_terminal_size().columns
                npn = np.as_posix()
                msg = f'{p.name} -> {npn}'
                if len(msg) > max_width:
                    print(f'\n{p.name}\n↓\n{npn}')
                else:
                    print(msg)
            else:
                p.rename(np)
