import argparse
import json
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any, Dict

from pack.utils import parse_bool, shell

_zshcom = None
_transient = None
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
class _Exporter:
    func: Callable
    mutate: _ExportValMutator


_exports: Dict[str, _Exporter] = {}


def _export(name, mutator: _ExportValMutator):
    def wrapper(func):
        _exports[name] = _Exporter(func, mutator)

    return wrapper


class Config:

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
    def base_dir(self) -> Path:
        if _zshcom is not None:
            return _zshcom

        return self._get_path(_CP(None, 'ZSHCOM__basedir'))

    @_export('ZSHCOM_PYTHON', lambda v: v.as_posix())
    def python_bin(self) -> Path:
        return self._get_path(_CP('python', 'ZSHCOM_PYTHON'))

    @_export('ZSHCOM__transient', lambda v: v.as_posix())
    def transient(self) -> Path:
        k = _CP('transient', 'ZSHCOM_TRANSIENT')
        r = self._get_path(k, False)

        if r is None:
            r = _transient

        if r is None:
            raise Exception(f'.{k.file_key} is missing. Export in .ztk.json or {k.env_key} environment variable')
        elif not r.exists():
            raise Exception(f'.{k.file_key} path {r.as_posix()} is missing. Export in .ztk.json or {k.env_key} environment variable')

        return r

    @_export('ZSHCOM__cache', lambda v: v.as_posix())
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
    def banner(self) -> Path:
        return self._get_path(_CP('banner', 'ZSHCOM_BANNER'), False)

    @_export('ZSHCOM_HIDE_SPLASH', str)
    def hide_splash(self) -> bool:
        return self._get_bool(_CP('hideSplash', 'ZSHCOM_HIDE_SPLASH'), False)


def find_transient() -> Path | None:
    if platform.system() == 'Windows':
        return Path('/tmp/zsh_toolkit')
    else:
        dfr = shell('df').split('\n')
        rx = re.compile(r'^tmpfs.+(/dev/shm|/run/user)')
        mounts = []

        for l in dfr:
            m = rx.match(l)

            if m and m.group(1):
                mounts.append(m.group(1))

        runusr = Path(f'/run/user/{os.getuid()}')

        if '/run/user' in mounts and runusr.is_dir():
            r = runusr / 'ztk'

            if not r.exists():
                # noinspection PyBroadException
                try:
                    r.mkdir()
                except:
                    pass

            return r

        devshm = '/dev/shm'

        if devshm in mounts:
            r = Path(devshm) / 'ztk'

            if not r.exists():
                # noinspection PyBroadException
                try:
                    r.mkdir()
                except:
                    pass

            return r

    return None


def _dump_exports(args):
    c = Config()

    if args.source:
        for k, e in _exports.items():
            v = e.func(c)
            if v is not None:
                v = e.mutate(v)
            if v is not None:
                print(f'export {k}={v}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('zshcom', type=str, help='ZSHCOM environment variable')
    parser.add_argument('--source', action='store_true', help='Print out for zsh sourcing')
    _args = parser.parse_args()

    _zshcom = Path(_args.zshcom)

    if not _zshcom.exists():
        raise Exception(f'ZSHCOM dir doesn\'t exist')

    if _args.source:
        _transient = find_transient()
        _dump_exports(_args)
