import json
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any, Dict, Generator

# noinspection PyUnresolvedReferences
from pack.utils import parse_bool, shell

_ztk_file_config_path = Path('~/.ztk.json').expanduser().resolve()
_ztk_file_config: dict | None = None

if _ztk_file_config is None:
    if _ztk_file_config_path.exists():
        with _ztk_file_config_path.open() as f:
            _ztk_file_config = json.load(f)
    else:
        _ztk_file_config = {}


@dataclass
class _CP:
    file_key: str | None
    env_key: str


_ExportValMutator = Callable[[Any], str]


@dataclass()
class Exporter:
    func: Callable
    mutate: _ExportValMutator


_exports: Dict[str, Exporter] = {}


def _export(name, mutator: _ExportValMutator):
    def wrapper(func):
        _exports[name] = Exporter(func, mutator)
        return func

    return wrapper


def detect_transient_candidates() -> Generator[Path, None, None]:
    if platform.system() == 'Windows':
        yield Path('/tmp/zsh_toolkit')
    else:
        dfr = shell('df').split('\n')
        rx = re.compile(r'^tmpfs.+(/dev/shm|/run/user)')
        mounts = []

        for ln in dfr:
            m = rx.match(ln)

            if m and m.group(1):
                mounts.append(m.group(1))

        runusr = Path(f'/run/user/{os.getuid()}')

        if '/run/user' in mounts and runusr.is_dir():
            yield runusr / 'ztk'

        devshm = '/dev/shm'

        if devshm in mounts:
            yield Path(devshm) / 'ztk'


_zshcom: Path | None = None


class Config:

    def __init__(self, zshcom: Path = None):
        global _zshcom

        if zshcom:
            _zshcom = zshcom
        elif _zshcom is None:
            _zshcom = Config._get_path(_CP(None, 'ZSHCOM__basedir'), False)

        if _zshcom is None or not _zshcom.exists():
            raise Exception('Unable to get zsh-toolkit dir')

    @staticmethod
    def _get_export_funcs() -> Dict[str, Exporter]:
        return _exports

    @staticmethod
    def _get_str(k: _CP, fail_if_missing=True) -> str:
        if k.file_key and k.file_key in _ztk_file_config:
            v = _ztk_file_config[k.file_key]
        else:
            v = os.environ.get(k.env_key)

        if not fail_if_missing or v is not None:
            return v

        if k.file_key:
            raise Exception(f'.{k.file_key} setting missing. Set in .ztk.json or {k.env_key} environment variable')
        else:
            raise Exception(f'{k.env_key} missing. Export environment variable')

    @staticmethod
    def _get_path(k: _CP, fail_if_missing=True) -> Path | None:
        rv = Config._get_str(k, fail_if_missing)

        if rv is None and not fail_if_missing:
            return None

        v = Path(rv)

        if not fail_if_missing or v.exists():
            return v.expanduser().resolve()

        if k.file_key:
            raise Exception(f'.{k.file_key} path {v.as_posix()} is missing. Export in .ztk.json or {k.env_key} environment variable')
        else:
            raise Exception(f'{k.env_key} path {v.as_posix()} is missing. Export environment variable')

    @staticmethod
    def _get_bool(k: _CP, fail_if_missing=True) -> bool | None:
        rv = Config._get_str(k, fail_if_missing)
        v = parse_bool(rv)

        if not fail_if_missing or v is not None:
            return v

        if k.file_key:
            raise Exception(f'.{k.file_key} {rv} is invalid bool. Export in .ztk.json or {k.env_key} environment variable')
        else:
            raise Exception(f'{k.env_key} {rv} is invalid bool. Export environment variable')

    @_export('ZSHCOM__basedir', lambda v: v.as_posix())
    @property
    def base_dir(self) -> Path:
        if _zshcom is not None:
            return _zshcom

        return self._get_path(_CP(None, 'ZSHCOM__basedir'))

    @_export('ZSHCOM_PYTHON', lambda v: v.as_posix())
    @property
    def python_bin(self) -> Path:
        return self._get_path(_CP('python', 'ZSHCOM_PYTHON'))

    @_export('ZSHCOM__transient', lambda v: v.as_posix())
    @property
    def transient(self) -> Path:
        k = _CP('transient', 'ZSHCOM__transient')
        r = self._get_path(k, False)

        if r is None:
            for t in detect_transient_candidates():
                if t.exists():
                    r = t
                    break
                else:
                    # noinspection PyBroadException
                    try:
                        t.mkdir(parents=True)
                        r = t
                        break
                    except:
                        pass

        if r is None:
            print(f'.{k.file_key} is missing. Export in .ztk.json or {k.env_key} environment variable')
        elif not r.exists():
            print(f'.{k.file_key} path {r.as_posix()} is missing. Export in .ztk.json or {k.env_key} environment variable')

        return r

    @_export('ZSHCOM__cache', lambda v: v.as_posix())
    @property
    def cache(self) -> Path:
        k = _CP('cache', 'ZSHCOM_CACHE')
        r = self._get_path(k, False)

        if r is None:
            r = Path('~/.cache/ztk')

        r = r.expanduser().resolve()

        if not r.exists():
            r.mkdir(parents=True)
        elif r.is_file():
            raise Exception(f'.{k.file_key}/{k.env_key} path {r.as_posix()} is a file, must be directory')

        return r

    @_export('ZSHCOM__banner', lambda v: v.as_posix())
    @property
    def banner(self) -> Path:
        return self._get_path(_CP('banner', 'ZSHCOM_BANNER'), False)

    @_export('ZSHCOM_HIDE_SPLASH', str)
    @property
    def hide_splash(self) -> bool:
        return self._get_bool(_CP('hideSplash', 'ZSHCOM_HIDE_SPLASH'), False)

    @property
    def os(self):
        return self._get_str(_CP(None, 'ZSHCOM__known_os'), False)

    @property
    def hw(self):
        return self._get_str(_CP(None, 'ZSHCOM__known_hw'), False)
