import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import emoji

from zsh_toolkit_py.shared.utils import ShellColors, Ask

_ask = Ask()

_need_dump_replacements = False
_char_replacements_changed = False
_char_replacements_file_loaded = False
_char_replacements_file = Path.home() / '.double_byte_replacements'
_char_replacements: Dict[str, str] = {}
_char_replacements_inverted: Dict[str, str] = {}
_char_removes = []
_mark_char = os.environ.get('ZSHCOM_TEXT_HIGHLIGHT')

if _mark_char:
    _mark_char = bytes(_mark_char, "utf-8").decode('unicode_escape')
else:
    _mark_char = ShellColors.Black + ShellColors.Highlight_Yellow


@dataclass
class Replacement:
    original: str
    clean: str
    highlighted: str


_filler_chars = '_-'
_rx_consecutive_filler_chars: re.Pattern = re.compile(r'([_-])[_-]+')
_rx_space: re.Pattern = re.compile(r'\s+')


def remove_consecutive_filler_chars(string: str, lstrip: bool = False, rstrip: bool = False) -> str:
    lv = None
    cv = string

    while lv != cv:
        lv = cv
        cv = re.sub(_rx_space, ' ', cv)
        cv = re.sub(_rx_consecutive_filler_chars, r'\1', cv)
        if rstrip:
            cv = cv.rstrip(_filler_chars + ' ')
        if lstrip:
            cv = cv.lstrip(_filler_chars + ' ')

    return cv


def _load_replacements() -> None:
    global _char_replacements_file_loaded

    if _char_replacements_file_loaded or not _char_replacements_file.exists():
        return

    with _char_replacements_file.open('r') as f:
        for line in f.readlines():
            if line.startswith('!rm\t'):
                char_removes = line[4:]

                for c in char_removes:
                    if c == '\r' or c == '\n':
                        continue
                    _char_removes.append(c)
            else:
                replacement = line[0]
                _char_replacements[replacement] = ''
                for c in list(line)[1:]:
                    if c == '\r' or c == '\n':
                        continue
                    _char_replacements[replacement] += c
                    _char_replacements_inverted[c] = replacement

    _char_replacements_file_loaded = True


def _dump_replacements() -> None:
    global _need_dump_replacements
    global _char_replacements_changed

    if _need_dump_replacements:
        if not _char_replacements_changed and _char_replacements_file.exists():
            _char_replacements_file.rename(_char_replacements_file.parent / f'{_char_replacements_file.name}.bak')

        if not _char_replacements_changed:
            _char_replacements_changed = True

        contents = ''

        if len(_char_removes) > 0:
            contents += f'!rm\t'

            for c in _char_removes:
                contents += f'{c}'

        for k in _char_replacements.keys():
            if contents:
                contents += '\n'
            contents += f'{k}{_char_replacements[k]}'

        with _char_replacements_file.open('w') as f:
            f.write(contents)

        _need_dump_replacements = False


def _replace_dbl_byte_char(char: str, before: str, after: str, keep_emoji: bool) -> str:
    global _need_dump_replacements

    if char in _char_replacements_inverted:
        return _char_replacements_inverted[char]
    elif emoji.is_emoji(char):
        return char if keep_emoji else ''
    else:
        print(f'New double byte char found: {before}{_mark_char}{char}{ShellColors.Off}{after}')
        repl_char = None

        while repl_char is None:
            resp = _ask.char('Character to replace it with', also_valid=['!rm'])

            if resp is None:
                continue

            if resp == '!rm':
                resp2 = _ask.yes_no(f'Remove future instances of {char} perpetually', empty_is_true=True)

                if resp2:
                    repl_char = ''
            else:
                resp2 = _ask.yes_no(f'Replace future instances of {char} with {resp} perpetually', empty_is_true=True)

                if resp2:
                    repl_char = resp

        if repl_char == '':
            _char_removes.append(char)
        else:
            _char_replacements_inverted[char] = repl_char
            if repl_char not in _char_replacements:
                _char_replacements[repl_char] = ''
            _char_replacements[repl_char] += char

        _need_dump_replacements = True
        return repl_char


def replace_dbl_byte_chars(s: str, keep_emoji: bool = False) -> Replacement:
    _load_replacements()
    clean = ''
    highlighted = ''
    ci = 0

    for c in s:
        if len(c.encode('utf-8')) > 1:
            nc = _replace_dbl_byte_char(c, clean, s[ci + 1:], keep_emoji)
            if nc:
                clean += nc
                highlighted += f'{_mark_char}{nc}{ShellColors.Off}'
        else:
            clean += c
            highlighted += c

        ci += 1

    _dump_replacements()

    return Replacement(s, clean, highlighted)
