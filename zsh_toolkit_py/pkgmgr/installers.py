import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Union, List, Tuple

from zsh_toolkit_py.shared.utils import shell


def _sudo(cmd: List[str]) -> Tuple[int, str, str]:
    cmd = ['sudo'] + cmd
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    data = p.communicate()

    return (p.returncode, data[0].decode(), data[1].rstrip(b'\n').decode())


class PackageManagers(Enum):
    pipx = 'pipx'
    pipx_local = 'pipx_local'
    pacman = 'pacman'
    apt = 'apt'


@dataclass
class PackageInfo:
    package_manager: str
    name: str
    installed: bool
    has_update: bool


class PackageManager:

    # noinspection PyMethodMayBeStatic
    def log(self, msg: str) -> None:
        print(f'[{self.name()}]\t{msg}')

    def name(self) -> str:
        pass

    def install(self, pkg_name: str) -> None:
        pass

    def can_update(self) -> bool:
        return False

    def update(self, pkg_name: str) -> None:
        pass

    def get_info(self, pkg_name: str) -> PackageInfo:
        pass


class Pacman(PackageManager):

    def __init__(self) -> None:
        self._pipx_packages = None

    def name(self) -> str:
        return PackageManagers.pacman.value

    def install(self, pkg_name: str) -> None:
        self.log(f'installing {pkg_name} (requires sudo)')

        r = _sudo(['pacman', "--noconfirm", '-S', pkg_name])

        if r[0] != 0:
            raise Exception(f'Failed to install: {r[2]}')

    def get_info(self, pkg_name: str) -> PackageInfo:
        r = shell(f'pacman -Q {pkg_name} && echo good', suppress_error=True)

        if r.endswith('good'):
            return PackageInfo(self.name(), pkg_name, True, False)
        else:
            return PackageInfo(self.name(), pkg_name, False, False)


class Apt(PackageManager):
    _installed_rx = re.compile(r'\[[^]]*?installed[^]]*?\]')

    def __init__(self) -> None:
        self._pipx_packages = None

    def name(self) -> str:
        return PackageManagers.apt.value

    def install(self, pkg_name: str) -> None:
        self.log(f'installing {pkg_name} (requires sudo)')

        r = _sudo(['apt', 'install', '-y', pkg_name])

        if r[0] != 0:
            raise Exception(f'Failed to install: {r[2]}')

    def get_info(self, pkg_name: str) -> PackageInfo:
        r = shell(f'apt list {pkg_name}', suppress_error=True)

        if self._installed_rx.findall(r):
            return PackageInfo(self.name(), pkg_name, True, False)
        else:
            return PackageInfo(self.name(), pkg_name, False, False)


_pipx_list_re = re.compile(r'^(\S+)\s+(.+)$')


class PipX(PackageManager):
    # ToDo: Figure out how to properly pull from py.pack
    _zsh_toolkit_version: str
    _python_bin: str
    _pipx_packages: Union[Dict[str, str], None]

    def __init__(self, zsh_toolkit_version: str, python_bin: str) -> None:
        self._zsh_toolkit_version = zsh_toolkit_version
        self._python_bin = python_bin
        self._pipx_packages = None

    def name(self) -> str:
        return PackageManagers.pipx.value

    def install(self, pkg_name: str) -> None:
        self.log(f'installing {pkg_name}')

        shell(f'pipx install {pkg_name} --python="{self._python_bin}"m')

    def can_update(self) -> bool:
        return True

    def update(self, pkg_name: str) -> None:
        self.log(f'Upgrading {pkg_name}')

        shell(f'pipx upgrade {pkg_name}')

    def get_info(self, pkg_name: str) -> PackageInfo:
        if self._pipx_packages is None:
            res = shell('pipx list --short')

            for ln in res.splitlines():
                m: re.Match = re.search(_pipx_list_re, ln)

                if m:
                    if self._pipx_packages is None:
                        self._pipx_packages = {}

                    self._pipx_packages[m.group(1)] = m.group(2)
                else:
                    self.log(f'pipx list: Failed to parse line {ln}')

        if self._pipx_packages is None:
            self.log('No pipx packages found')
            return PackageInfo(self.name(), pkg_name, False, False)

        if pkg_name == 'zsh_toolkit_py':
            if pkg_name not in self._pipx_packages:
                return PackageInfo(self.name(), pkg_name, False, False)
            elif self._pipx_packages[pkg_name] != self._zsh_toolkit_version:
                return PackageInfo(self.name(), pkg_name, True, True)
            else:
                return PackageInfo(self.name(), pkg_name, True, False)
        else:
            # ToDo: Check for update
            if pkg_name not in self._pipx_packages:
                return PackageInfo(self.name(), pkg_name, False, False)
            else:
                return PackageInfo(self.name(), pkg_name, True, False)


class PipXLocal(PipX):

    def __init__(self, zsh_toolkit_version: str, python_bin: str) -> None:
        super().__init__(zsh_toolkit_version, python_bin)

    def name(self) -> str:
        return PackageManagers.pipx_local.value

    def install(self, pkg_name: str) -> None:
        raise "PipXLocal doesn't support this functionality"

    def install_local(self, pkg_name: str, path: Path) -> None:
        self.log(f'installing {pkg_name}')
        shell(f'pipx install -e "{path.as_posix()}" --python="{self._python_bin}"')


_constructors = {
    PackageManagers.pacman.value: Pacman,
    PackageManagers.apt.value: Apt
}


def package_manager_factory(key: str) -> Union[PackageManager | None]:
    return _constructors[key]() if key in _constructors else None
