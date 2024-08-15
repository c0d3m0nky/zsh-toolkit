import os
from pathlib import Path
from typing import List, Union

ztk_base_dir = Path(os.environ.get('ZSHCOM__basedir')).resolve()

ztk_ram_cache: Union[Path, None] = os.environ.get('ZSHCOM__transient')

if ztk_ram_cache:
    ztk_ram_cache: Path = Path(os.environ.get('ZSHCOM__transient')).resolve()
else:
    ztk_ram_cache = None

dependencies_checked = ztk_base_dir / '.state_dependencies_checked'
update_dependencies = ztk_base_dir / '.state_update_dependencies'
trigger_re_source = ztk_base_dir / '.state_trigger_resource'
trigger_update = ztk_base_dir / '.state_trigger_update'
repo_update_checked = ztk_base_dir / '.state_repo_update_checked'
repo_updated = ztk_base_dir / '.state_repo_updated'
init_data = ztk_base_dir / 'initData.json'

_cache_prefixes: List[str] = ['.var_', '.cache_', '.state_']
_clear_cache_exclude: List[str] = ['.state_repo_update_checked']


def clear_cache():
    for f in ztk_base_dir.iterdir():
        if f.is_file() and f.name not in _clear_cache_exclude and any([f.name.startswith(p) for p in _cache_prefixes]):
            f.unlink()
