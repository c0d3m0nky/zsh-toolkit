from datetime import datetime, timedelta
from pathlib import Path
import os
import json
import subprocess
import shutil

from typing import Union, Dict

from pack.constants import zsh_toolkit_version
from pkgmgr.models import InitData

import pack.magic_files as mf
from pkgmgr.installers import PipX, PackageManager, PackageInfo, PipXLocal, package_manager_factory

ZSHCOM_PYTHON = os.environ.get("ZSHCOM_PYTHON")


def set_parent_var(var: str, value: str):
    with open(mf.ztk_base_dir / f'.var_{var}', 'w') as text_file:
        text_file.write(value)


def _sh(cmd: str, check=False, suppress_error=False) -> str:
    if suppress_error:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=check)
    else:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=check)

    return res.stdout.decode('utf-8').strip()


def _pkg_check_os() -> bool:
    return True


# ToDo: Get rid of this
_os = os.environ.get('ZSHCOM__known_os')
_package_manager = os.environ.get('ZSHCOM__pkg_man')

_pipx = PipX(zsh_toolkit_version, ZSHCOM_PYTHON)
_pipx_local = PipXLocal(zsh_toolkit_version, ZSHCOM_PYTHON)
_os_pm: Union[PackageManager, None] = None

_package_managers: Dict[str, PackageManager] = {
    _pipx.name(): _pipx,
    _pipx_local.name(): _pipx_local
}

if _package_manager:
    _os_pm = package_manager_factory(_package_manager)

    if _os_pm is not None:
        _package_managers[_os_pm.name()] = _os_pm


def init():
    if not mf.repo_update_checked.exists() or datetime.fromtimestamp(mf.repo_update_checked.stat().st_mtime) < (
            datetime.now() - timedelta(days=7)):
        if shutil.which('_ztk-update') is None:
            print('ztk updater seems to be missing')
        else:
            resp = input(
                f'You have not checked for zsh-toolkit updates in over a week, would you like to check now: ').strip()

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
        pkg_info = PackageInfo('', '', False, False)

        if pkg.pipx:
            pkg_info = _pipx.get_info(pkg.pipx)
        elif pkg.pipx_local:
            pkg_info = _pipx_local.get_info(pkg.pipx)

        if not pkg_info.installed and _os_pm and _os_pm.name() in pkg.fields:
            pkg_info = _os_pm.get_info(pkg.fields[_os_pm.name()])

        if _os_pm and not pkg_info.installed and pkg.os:
            pkg_info = _os_pm.get_info(pkg.os)

        if _os_pm and not pkg_info.installed and pkg.os:
            pkg_info = _os_pm.get_info(pkg.os)

        if not pkg_info.installed and pkg.which:
            if _sh(f'which {pkg.which}'):
                pkg_info = PackageInfo('', '', True, False)

        satisfied = False

        if not pkg_info.installed and pkg_info.package_manager:
            try:
                if pkg.pipx:
                    _pipx.install(pkg.pipx)
                    satisfied = True
                elif pkg.pipx_local:
                    p = Path(pkg.pipx_local)

                    if not p.is_absolute():
                        p = mf.ztk_base_dir / p

                    _pipx_local.install_local(pk, p.resolve())
                    satisfied = True
                elif _os_pm.name() in pkg.fields:
                    _os_pm.install(pkg.fields[_os_pm.name()])
                    satisfied = True
                elif pkg.os:
                    _os_pm.install(pkg.os)
                    satisfied = True
            except Exception as e:
                print('')
                print(f'Failed to install {pk} with {pkg_info.package_manager} ({pkg_info.name}): {e}')
                satisfied = False
        elif pkg_info.has_update and pkg_info.package_manager in _package_managers:
            # ToDo: Make this work for more than just pipx local
            pm = _package_managers[pkg_info.package_manager]

            if pm.can_update():
                try:
                    pm.update(pkg_info.name)
                    satisfied = True
                except Exception as e:
                    print('')
                    print(f'Failed to update {pk} with {pkg_info.package_manager}: {e}')
                    satisfied = False
        elif pkg_info.installed:
            satisfied = True

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

            details = mp.details(_package_manager).replace("\t", "\n\t\t")
            print(f'\t{pk}:\t{"REQUIRED" if mp.required else ""}\n\t\t{details}')

        if any_required:
            exit(1)

    # ToDo: recheck ZSHCOM__feat_* done in init
    mf.dependencies_checked.touch()

    if mf.update_dependencies.exists():
        mf.update_dependencies.unlink()


init()
