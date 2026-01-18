from typing import List
from itertools import chain

# noinspection PyUnresolvedReferences
import zsh_toolkit_py.shared.config as config

_config = config.Config()
_transient = _config.transient

if not _transient:
    raise Exception('Could not determine transient dir location')
elif not _transient.exists():
    try:
        _transient.mkdir(parents=True)
    except Exception as e:
        raise Exception(f'Failed to create Transient dir @ {_transient.resolve().as_posix()} : {e}')

ztk_base_dir = _config.base_dir

dependencies_checked = _transient / '.state_dependencies_checked'
update_dependencies = _transient / '.state_update_dependencies'
trigger_re_source = _transient / '.state_trigger_resource'
trigger_update = _transient / '.state_trigger_update'
repo_update_checked = _config.cache / '.state_repo_update_checked'
repo_updated = _config.cache / '.state_repo_updated'
init_data = _config.base_dir / 'initData.json'
init = _config.base_dir / 'init.zsh'
break_init = _transient / '.state_break_init'

_cache_prefixes: List[str] = ['.var_', '.cache_', '.state_']
_clear_cache_exclude: List[str] = ['.state_repo_update_checked']


def clear_cache():
    for f in chain(_config.base_dir.iterdir(), _config.base_dir.iterdir()):
        if f.is_file() and f.name not in _clear_cache_exclude and any([f.name.startswith(p) for p in _cache_prefixes]):
            f.unlink()
