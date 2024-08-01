import os
from pathlib import Path
from typing import List

ztk_basedir = Path(os.environ.get('ZSHCOM__basedir')).resolve()
dependencies_checked = ztk_basedir / '.state_dependencies_checked'
update_dependencies = ztk_basedir / '.state_update_dependencies'
trigger_re_source = ztk_basedir / '.state_trigger_resource'
trigger_update = ztk_basedir / '.state_trigger_update'
repo_update_checked = ztk_basedir / '.state_repo_update_checked'
repo_updated = ztk_basedir / '.state_repo_updated'
init_data = ztk_basedir / 'initData.json'


_cache_prefixes: List[str] = ['.var_', '.cache_', '.state_']


def clear_cache():
    for f in ztk_basedir.iterdir():
        if f.is_file() and any([f.name.startswith(p) for p in _cache_prefixes]):
            f.unlink()
