import platform
import re

from pathlib import Path
from typing import Union, Dict, List, Generator, Tuple

from init_models import SystemInfo


# region bootstrapping

def _read_lines(file_path: Path) -> Generator[str, None, None]:
    if file_path.exists():
        with file_path.open('r') as f:
            for l in f:
                yield l.strip()


class InfoFileField:
    value: Union[List[str], None]

    def __init__(self, value: Union[str, List[str], None] = None) -> None:
        val = []

        if type(value) is list:
            for vv in value:
                vc = vv.strip()

                if vc:
                    val.append(vc)
        elif type(value) is str:
            val.append(value)

        self.value = val if len(val) > 0 else None

    def is_match(self, p: Union[str, re.Pattern]) -> bool:
        if self.value is None:
            return False

        if type(p) is str:
            for v in self.value:
                if re.match(p, v):
                    return True
        else:
            for v in self.value:
                if p.match(v):
                    return True

        return False

    def __contains__(self, p: Union[str, re.Pattern]) -> bool:
        if self.value is None:
            return False

        if type(p) is re.Pattern:
            return self.is_match(p)
        else:
            for v in self.value:
                if p in v:
                    return True

            return False

    def __eq__(self, other) -> bool:
        if isinstance(other, InfoFileField):
            return self.value == other.value

        if type(other) is str:
            for v in self.value:
                if other == v:
                    return True

        return False


class OsRelease:
    _re: re.Pattern = re.compile(r'^([^=\s]+)="?([^"]+)"?$')
    fields: Dict[str, str]
    id: InfoFileField
    like: InfoFileField
    version: InfoFileField
    name: InfoFileField

    def __init__(self):
        self.fields = {}

        for l in _read_lines(Path('/etc/os-release')):
            m = self._re.match(l)

            if m:
                self.fields[m.group(1).lower()] = m.group(2).strip()

        def get_field(*names: str) -> InfoFileField:
            res = []

            for name in names:
                if name in self.fields:
                    res.append(self.fields[name])

            return InfoFileField(res)

        self.id = get_field('id')
        self.like = get_field('id_like', 'like')
        self.version = get_field('version', 'version_codename')
        self.name = get_field('name', 'pretty_name')


class CpuInfo:
    _re: re.Pattern = re.compile(r'^([^:\s]+)\s*?:\s*?(.+)$')
    cpu_count: Union[int, None]
    model: InfoFileField

    def __init__(self):
        self.model = InfoFileField()
        self.cpu_count = None

        for l in _read_lines(Path('/proc/cpuinfo')):
            m = self._re.match(l)

            if m:
                k = m.group(1).lower()
                v = m.group(2).strip()

                if k == 'processor':
                    if self.cpu_count is None:
                        self.cpu_count = 1
                    else:
                        self.cpu_count += 1

                if k == 'model':
                    self.model = InfoFileField(v)


# endregion


basic_distro_checks: Dict[str, Tuple[str, str, Union[str, None]]] = {
    'arch': ('=', 'arch', 'pacman'),
    'alpine': ('=', 'alpine', 'apk'),
    'pop': ('=', 'pop', 'apt'),
    'ubuntu': ('=', 'ubuntu', 'apt'),
    'debian': ('*', 'debian', 'apt'),
    'slackware': ('=', 'unraid', None),
}


def get_system_info() -> SystemInfo:
    r = SystemInfo()

    if platform.system() == 'Linux':
        osr = OsRelease()
        cpu = CpuInfo()

        if cpu.cpu_count:
            r.hardware.cpu_cores = cpu.cpu_count

        if cpu.model and cpu.model.is_match(r'model\s+:\s+raspberry'):
            r.hardware.code = 'pi'

        if Path('/.dockerenv').exists():
            r.hardware.code = 'docker'

        def check_distro() -> bool:
            for kk in basic_distro_checks:
                d = basic_distro_checks[kk]

                if d[0] == '=':
                    if kk == osr.id or kk == osr.like:
                        r.os.code = d[1]
                        if d[2] is not None:
                            r.os.pkg_mgr = d[2]
                        return True
                elif d[0] == '*':
                    if kk in osr.id or kk in osr.like:
                        r.os.code = d[1]
                        if d[2] is not None:
                            r.os.pkg_mgr = d[2]
                        return True

            return False

        if not check_distro():
            # put weird ones here
            pass

    elif platform.system() == 'Windows':
        r.os.code = 'win'
    elif platform.system() == 'Darwin':
        r.os.code = 'osx'

    return r
