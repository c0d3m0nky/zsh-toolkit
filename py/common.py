import sys
from argparse import ArgumentParser
from pathlib import Path
import re
import os
import platform
import json
import subprocess

from typing import Union, Dict, List


class PipPkg:
    pip: str = None
    pipx: str = None
    pipx_local: str = None
    pacman: str = None
    required: bool = False

    def __init__(self, pip: str = None, pipx: str = None, pipx_local: str = None, pacman: str = None, required: bool = False) -> None:
        self.pip = pip
        self.pipx = pipx
        self.pipx_local = pipx_local
        self.pacman = pacman
        self.required = required

    def __str__(self) -> str:
        op = []

        if self.pip:
            op.append(f'pip: {self.pip}')
        if self.pacman:
            op.append(f'pacman: {self.pacman}')
        if self.pipx_local:
            op.append(f'pipx_local: {self.pipx_local}')
        if self.pipx:
            op.append(f'pipx: {self.pipx}')

        return '\t'.join(op)


class InitData:
    pip: Dict[str, PipPkg] = {}

    def __init__(self, pip: Dict[str, Dict[str, str]] = None) -> None:
        for pk in pip:
            self.pip[pk] = PipPkg(**pip[pk])


def parse_bool(s: str) -> Union[bool, None]:
    if s:
        s = s.lower()
        if s in ['yes', 'true', 't', 'y', '1']:
            return True
        elif s in ['no', 'false', 'f', 'n', '0']:
            return False
        else:
            return None
    else:
        return None


_basedir = Path(os.environ.get('ZSHCOM__basedir'))
_pip_arch = parse_bool(os.environ.get('ZSHCOM_PIP_ARCH'))
_pip_install_user: bool = parse_bool(os.environ.get('ZSHCOM_PIP_INSTALL_USER')) or True

if _pip_arch is None:
    _pip_arch = platform.system() == 'Linux' and platform.freedesktop_os_release()['ID_LIKE'] == 'arch'

with open(_basedir / 'initData.json') as jf:
    mp = json.load(jf)

_init_data = InitData(**mp)


def _sh(cmd: str, check=False) -> str:
    res = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=check)
    return res.stdout.decode('utf-8').strip()


def _pip_install_pip(pkg: str):
    print(f'installing {pkg}')
    if _pip_install_user:
        _sh(f'pip3 install --user {pkg}', check=True)
    else:
        _sh(f'pip3 install {pkg}', check=True)


def _pip_upgrade_pipx(pkg: str, local: Path = None):
    print(f'Upgrading {pkg}')
    if local:
        _sh(f'pipx upgrade {pkg}', check=True)
    else:
        _sh(f'pipx upgrade {pkg}', check=True)


def _pip_install_pipx(pkg: str, local: Path = None):
    print(f'installing {pkg}')
    if local:
        _sh(f'pipx install -e "{local.as_posix()}"', check=True)
    else:
        _sh(f'pipx install {pkg}', check=True)


def _pip_check_pip(pkg: str) -> bool:
    return False


_pipx_packages: List[str] = None
_pipx_list_re = re.compile(r'^([^ ]+) ([\d.]+)$')


def _pip_check_pipx(pkg: str) -> bool:
    global _pipx_packages

    if _pipx_packages is None:
        res = _sh('pipx list --short')

        for l in res.splitlines():
            m: re.Match = re.search(_pipx_list_re, l)

            if m:
                if _pipx_packages is None:
                    _pipx_packages = []

                _pipx_packages.append(m.group(1))
            else:
                print(f'pipx list: Failed to parse line {l}')

    return pkg in _pipx_packages


def _pip_check_pacman(pkg: str) -> bool:
    r = _sh(f'pacman -Q {pkg} && echo good')

    return r.endswith('good')


_missing_packages = {}

for pk in _init_data.pip:
    pkg = _init_data.pip[pk]
    satisfied = False

    if _pip_check_pip(pkg.pip):
        satisfied = True
    elif pkg.pacman and _pip_check_pacman(pkg.pacman):
        satisfied = True
    elif pkg.pipx and _pip_check_pipx(pkg.pipx):
        satisfied = True
    elif pkg.pipx_local and _pip_check_pipx(pk):
        satisfied = True

    if not satisfied:
        if pkg.pip and not _pip_arch:
            try:
                _pip_install_pip(pkg.pip)
                satisfied = True
            except Exception as e:
                print('')
                print(f'Failed to install {pk} with pip')
                satisfied = False
        elif pkg.pacman and _pip_arch:
            print(f'Cannot install {pk} with pacman because it requires sudo. Please install manually')
            satisfied = False
        elif pkg.pipx_local:
            try:
                spec_path = Path(pkg.pipx_local)

                if not spec_path.is_absolute():
                    spec_path = Path(_basedir / pkg.pipx_local).resolve()

                _pip_install_pipx(pk, local=spec_path)
                satisfied = True
            except Exception as e:
                print('')
                print(f'Failed to install {pk} with pipx ({pkg.pipx_local})')
                satisfied = False
        elif pkg.pipx:
            try:
                _pip_install_pipx(pkg.pipx, pk)
                satisfied = True
            except Exception as e:
                print('')
                print(f'Failed to install {pk} with pipx')
                satisfied = False

    if not satisfied:
        _missing_packages[pk] = pkg

if _missing_packages:
    any_required = False
    print('')
    print('Missing packages:')

    for pk in _missing_packages:
        mp = _missing_packages[pk]

        if mp.required:
            any_required = True

        print(f'\t{pk}:\t{"REQUIRED" if mp.required else ""}\n\t\t{str(mp).replace("\t", "\n\t\t")}')

    if any_required:
        exit(1)


# ToDo: Move to pipx package
def zshrc_rxmv(args):
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
    args = ap.parse_args(args)

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
                    if not psx in mkdirs:
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


if sys.argv[1] == '_funcs':
    for name, value in [(k, v) for k, v in vars().items()]:
        if not name.startswith("zshrc_") or not callable(value):
            continue
        print(name.replace('zshrc_', ''))
    exit(0)

_func = sys.argv[1]
_args = sys.argv[2:]
locals()['zshrc_' + _func](_args)
