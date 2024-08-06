import os

from pathlib import Path
from typing import Dict

import emoji
from tap import Tap
from userinput import userinput

from utils import parse_bool, ShellColors


class Args(Tap):
    plan: bool = False

    def configure(self) -> None:
        self.description = "Replace double byte chars in file & folder names"
        self.add_argument('-p', "--plan", action='store_true', help="Don't commit renames")


_args: Args
_dump_replacements = False
_char_replacements_changed = False
_char_replacements_file = Path.home() / '.double_byte_replacements'
_char_replacements: Dict[str, str] = {}
_char_replacements_inverted: Dict[str, str] = {}
_mark_char = os.environ.get('ZSHCOM_TEXT_HIGHLIGHT')

if _mark_char:
    _mark_char = bytes(_mark_char, "utf-8").decode('unicode_escape')
else:
    _mark_char = ShellColors.BLACK + ShellColors.Highlight_Yellow


def load_replacements() -> None:
    if not _char_replacements_file.exists():
        return

    with _char_replacements_file.open('r') as f:
        for line in f.readlines():
            replacement = line[0]
            _char_replacements[replacement] = ''
            for c in list(line)[1:]:
                if c == '\r' or c == '\n':
                    continue
                _char_replacements[replacement] += c
                _char_replacements_inverted[c] = replacement


def dump_replacements() -> None:
    global _dump_replacements
    global _char_replacements_changed

    if not _char_replacements_changed and _char_replacements_file.exists():
        _char_replacements_file.rename(_char_replacements_file.parent / f'{_char_replacements_file.name}.bak')

    if not _char_replacements_changed:
        _char_replacements_changed = True

    contents = ''

    for k in _char_replacements.keys():
        if contents:
            contents += '\n'
        contents += f'{k}{_char_replacements[k]}'

    with _char_replacements_file.open('w') as f:
        f.write(contents)

    _dump_replacements = False


def replace_char(char: str, before: str, after: str) -> str:
    global _dump_replacements

    if char in _char_replacements_inverted:
        return _char_replacements_inverted[char]
    elif emoji.is_emoji(char):
        return ''
    else:
        print(f'New double byte char found: {before}{_mark_char}{char}{ShellColors.OFF}{after}')
        repl_char = None

        while repl_char is None:
            resp = userinput('', label='Character to replace it with', cache=False)

            if resp is None:
                continue

            if len(resp) > 1:
                print('Too many characters')
            elif resp == '':
                print('Cannot replace with empty string')
            else:
                resp2 = parse_bool(userinput('', label=f'Replace future instances of {char} with {resp} perpetually', cache=False), True)

                if resp2:
                    repl_char = resp

        _char_replacements_inverted[char] = repl_char
        if repl_char not in _char_replacements:
            _char_replacements[repl_char] = ''
        _char_replacements[repl_char] += char
        _dump_replacements = True
        return repl_char


def rel_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def main():
    global _args
    _args = Args().parse_args()
    root = Path('./').resolve()
    load_replacements()

    for fso in root.iterdir():
        new_name = ''
        highlighted_name = ''
        ci = 0

        for c in fso.name:
            if len(c.encode('utf-8')) > 1:
                nc = replace_char(c, new_name, fso.name[ci + 1:])
                if nc:
                    new_name += nc
                    highlighted_name += f'{_mark_char}{nc}{ShellColors.OFF}'
            else:
                new_name += c
                highlighted_name += c

            ci += 1

        if new_name != fso.name:
            nf = fso.parent / new_name

            if nf.exists():
                print(f'{rel_path(root, nf)} exists')
            else:
                resp = parse_bool(userinput('', label=f'Rename file? {highlighted_name}', cache=False), True)

                if resp:
                    if _dump_replacements:
                        dump_replacements()

                    if _args.plan:
                        print(f'{rel_path(root, fso)} -> {rel_path(root, nf)}')
                    else:
                        fso.rename(nf)


if __name__ == '__main__':
    main()
