import os
from pathlib import Path
from typing import List
from itertools import chain

ztk_base_dir = Path(os.environ.get('ZSHCOM__basedir')).resolve()

_transient_env: str = os.environ.get('ZSHCOM__transient')

# ToDo: Stop doing this
if not _transient_env:
    raise Exception('!!! Transient files not supported, set ZSHCOM__transient in .zshrc')

ztk_transient: Path = Path(_transient_env).resolve()

dependencies_checked = ztk_transient / '.state_dependencies_checked'
update_dependencies = ztk_transient / '.state_update_dependencies'
trigger_re_source = ztk_transient / '.state_trigger_resource'
trigger_update = ztk_transient / '.state_trigger_update'
repo_update_checked = ztk_base_dir / '.state_repo_update_checked'
repo_updated = ztk_base_dir / '.state_repo_updated'
init_data = ztk_base_dir / 'initData.json'

_cache_prefixes: List[str] = ['.var_', '.cache_', '.state_']
_clear_cache_exclude: List[str] = ['.state_repo_update_checked']


def clear_cache():
    for f in chain(ztk_base_dir.iterdir(), ztk_transient.iterdir()):
        if f.is_file() and f.name not in _clear_cache_exclude and any([f.name.startswith(p) for p in _cache_prefixes]):
            f.unlink()
