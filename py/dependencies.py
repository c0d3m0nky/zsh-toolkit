from datetime import datetime, timedelta
from pathlib import Path
import re
import os
import platform
import json
import subprocess

from typing import Union, Dict, List

from pack.constants import zsh_toolkit_version
from pack.utils import parse_bool

import pack.magic_files as mf


def set_parent_var(var: str, value: str):
    with open(mf.ztk_base_dir / f'.var_{var}', 'w') as text_file:
        text_file.write(value)


class PipPkg:
    pip: str = None
    pipx: str = None
    pipx_local: str = None
    pacman: str = None
    required: bool = False
    # ToDo: implement
    os: bool

    # noinspection PyShadowingNames
    def __init__(self, pip: str = None, pipx: str = None, pipx_local: str = None, pacman: str = None, required: bool = False, os: bool = False) -> None:
        self.pip = pip
        self.pipx = pipx
        self.pipx_local = pipx_local
        self.pacman = pacman
        self.required = required
        self.os = os

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
    pkg: Dict[str, PipPkg] = {}

    def __init__(self, pkg: Dict[str, Dict[str, str]] = None) -> None:
        for pk in pkg:
            self.pkg[pk] = PipPkg(**pkg[pk])


_pip_arch = parse_bool(os.environ.get('ZSHCOM_PIP_ARCH'))
_pip_install_user: bool = parse_bool(os.environ.get('ZSHCOM_PIP_INSTALL_USER')) or True

if _pip_arch is None and platform.system() == 'Linux':
    os_release = getattr(platform, "freedesktop_os_release", None)
    if callable(os_release):
        _pip_arch = 'ID_LIKE' in platform.freedesktop_os_release() and platform.freedesktop_os_release()['ID_LIKE'] == 'arch'
    else:
        _pip_arch = False
else:
    _pip_arch = False


def _sh(cmd: str, check=False, suppress_error=False) -> str:
    if suppress_error:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=check)
    else:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=check)

    return res.stdout.decode('utf-8').strip()


def _pip_install_pip(pkg: str):
    print(f'installing {pkg}')
    if _pip_install_user:
        _sh(f'pip3 install --user {pkg}', check=True)
    else:
        _sh(f'pip3 install {pkg}', check=True)


def _pip_install_pacman(pkg: str):
    print(f'installing {pkg} (requires sudo)')

    cmd = ['sudo', 'pacman', "--noconfirm", '-S', pkg]
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    data = p.communicate()
    data = {"code": p.returncode, "stdout": data[0].decode(), "stderr": data[1].rstrip(b'\n').decode()}

    if data["code"] != 0:
        raise Exception("Failed to install: {0}".format(data["stderr"]))


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


_pip_list_re = re.compile(r'^([^\s]+)\s+(.+)$')
_pip_packages: Union[List[str], None] = None
_pipx_packages: Union[Dict[str, str], None] = None


def _pkg_check_os() -> bool:
    return True


def _pkg_check_pip(pkg: str) -> bool:
    global _pip_packages

    if _pip_packages is None:
        res = _sh('pip list')

        for ln in res.splitlines():
            if ln.startswith('Package') or ln.startswith('---'):
                continue

            m: re.Match = re.search(_pip_list_re, ln)

            if m:
                if _pip_packages is None:
                    _pip_packages = []

                _pip_packages.append(m.group(1))
            else:
                print(f'pip list: Failed to parse line {ln}')

    if _pip_packages is None:
        print('No pip packages found')
        return False

    return pkg in _pip_packages


def _pkg_check_pipx(pkg: str) -> str:
    global _pipx_packages

    if _pipx_packages is None:
        res = _sh('pipx list --short')

        for ln in res.splitlines():
            m: re.Match = re.search(_pip_list_re, ln)

            if m:
                if _pipx_packages is None:
                    _pipx_packages = {}

                _pipx_packages[m.group(1)] = m.group(2)
            else:
                print(f'pipx list: Failed to parse line {ln}')

    if _pipx_packages is None:
        print('No pipx packages found')
        return 'install'

    if pkg == 'zsh_toolkit_py':
        if pkg not in _pipx_packages:
            return 'install'
        elif _pipx_packages[pkg] != zsh_toolkit_version:
            return 'update'
        else:
            return ''
    else:
        if pkg not in _pipx_packages:
            return 'install'
        else:
            return ''


def _pkg_check_pacman(pkg: str) -> bool:
    r = _sh(f'pacman -Q {pkg} && echo good', suppress_error=True)

    return r.endswith('good')


def init():
    if not mf.repo_update_checked.exists() or datetime.fromtimestamp(mf.repo_update_checked.stat().st_mtime) < (datetime.now() - timedelta(days=7)):
        resp = input(f'You have not checked for zsh-toolkit updates in over a week, would you like to check now: ').strip()

        if resp.lower() == 'y':
            mf.trigger_update.touch()
            return

    if (mf.dependencies_checked.exists()
            and datetime.fromtimestamp(mf.dependencies_checked.stat().st_mtime) > (datetime.now() - timedelta(hours=24))
            and not mf.update_dependencies.exists()):
        return

    print('Checking dependencies...')

    with open(mf.init_data) as jf:
        mp = json.load(jf)

    init_data: InitData = InitData(**mp)

    missing_packages = {}

    for pk in init_data.pkg:
        pkg = init_data.pkg[pk]
        satisfied = False
        pipx_local_action = None

        if _pkg_check_pip(pkg.pip):
            satisfied = True
        elif pkg.pacman and _pkg_check_pacman(pkg.pacman):
            satisfied = True
        elif pkg.pipx and _pkg_check_pipx(pk) != 'install':
            satisfied = True
        elif pkg.pipx_local:
            pipx_local_action = _pkg_check_pipx(pk)
            if pipx_local_action == '':
                satisfied = True
        elif pkg.os and _pkg_check_os():
            satisfied = True

        if not satisfied:
            if pkg.pip and not _pip_arch:
                # noinspection PyBroadException
                try:
                    _pip_install_pip(pkg.pip)
                    satisfied = True
                except:
                    print('')
                    print(f'Failed to install {pk} with pip')
                    satisfied = False
            elif pkg.pacman and _pip_arch:
                try:
                    _pip_install_pacman(pkg.pacman)
                    satisfied = True
                except Exception as e:
                    print('')
                    print(f'Failed to install {pk} with pacman: {e}')
                    satisfied = False
            elif pkg.pipx_local:
                # noinspection PyBroadException
                try:
                    spec_path = Path(pkg.pipx_local)

                    if not spec_path.is_absolute():
                        spec_path = Path(mf.ztk_base_dir / pkg.pipx_local).resolve()

                    if pipx_local_action == 'install':
                        _pip_install_pipx(pk, local=spec_path)
                    else:
                        _pip_upgrade_pipx(pk, local=spec_path)
                    satisfied = True
                except:
                    print('')
                    print(f'Failed to install {pk} with pipx ({pkg.pipx_local})')
                    satisfied = False
            elif pkg.pipx:
                # noinspection PyBroadException
                try:
                    _pip_install_pipx(pkg.pipx)
                    satisfied = True
                except:
                    print('')
                    print(f'Failed to install {pk} with pipx')
                    satisfied = False

        if not satisfied:
            missing_packages[pk] = pkg

    if missing_packages:
        any_required = False
        print('')
        print('Missing packages:')

        for pk in missing_packages:
            mp = missing_packages[pk]

            if mp.required:
                any_required = True

            details = str(mp).replace("\t", "\n\t\t")
            print(f'\t{pk}:\t{"REQUIRED" if mp.required else ""}\n\t\t{details}')

        if any_required:
            exit(1)

    # ToDo: recheck ZSHCOM__feat_* done in init
    mf.dependencies_checked.touch()

    if mf.update_dependencies.exists():
        mf.update_dependencies.unlink()


init()
