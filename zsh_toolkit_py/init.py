import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Tuple, List

sys.path.append(Path(__file__).parent.parent.resolve().as_posix())

import shared.config as config
from init_models import SystemInfo, marshal_system_info


def _print_export(k: str, v: str | int):
    print(f'export {k}={v}')


def config_exports(c: config.Config):
    # noinspection PyProtectedMember
    for k, e in c._get_export_funcs().items():
        if type(e.func) is property:
            # noinspection PyTypeChecker
            p: property = e.func
            t = p.fget(c)
        else:
            t = e.func(c)

        if t is not None:
            t = e.mutate(t)
        if t is not None:
            _print_export(k, t)


def magic_files():
    import shared.magic_files as mf

    mfs: List[Tuple[str, Path]] = [t for t in [(a, getattr(mf, a)) for a in dir(mf) if not a.startswith('_') and not a.startswith('ztk_')] if isinstance(t[1], Path)]

    for t in mfs:
        _print_export(f'ZSHCOM__mf_{t[0]}', t[1].as_posix())


def system_info(cfg: config.Config):
    cache = cfg.cache / 'system.json'
    update_cache = False
    s: SystemInfo | None = None

    if cache.is_file():
        try:
            with cache.open('r') as f:
                s = marshal_system_info(json.load(f))
        except Exception as e:
            print(f'Failed to load {cache.name} from cache: {e}')

    if s is None:
        import system_info as si

        s = si.get_system_info()
        update_cache = True

    if s.os.code:
        _print_export('ZSHCOM__known_os', s.os.code)

    if s.os.pkg_mgr:
        _print_export('ZSHCOM__pkg_mgr', s.os.pkg_mgr)

    if s.hardware.code:
        _print_export('ZSHCOM__known_hw', s.hardware.code)

    if s.hardware.cpu_cores:
        _print_export('ZSHCOM__cpu_cores', s.hardware.cpu_cores)

    if update_cache:
        if cache.exists():
            if cache.is_file():
                cache.unlink()
            else:
                shutil.rmtree(cache)

        with cache.open('w') as f:
            json.dump(s, f, default=vars)


def _dump_exports(args, zshcom: Path):
    c = config.Config()

    config_exports(c)
    magic_files()
    system_info(c)


parser = argparse.ArgumentParser()
parser.add_argument('zshcom', type=str, help='ZSHCOM environment variable')
parser.add_argument('--source', action='store_true', help='Print out for zsh sourcing')
_args = parser.parse_args()

_zshcom = Path(_args.zshcom).expanduser().resolve()

if not _zshcom.exists():
    raise Exception(f"ZSHCOM dir doesn't exist")

if _args.source:
    _dump_exports(_args, _zshcom)
