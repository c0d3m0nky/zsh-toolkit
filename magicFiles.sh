#!/bin/zsh
# shellcheck disable=SC2034

if [[ -z "${ZSHCOM__transient}" || ! -d $(dirname "$ZSHCOM__transient") ]]; then
  echo "!!! Transient files not supported, set .transient in .ztk.json"
fi

mkdir -p "$ZSHCOM__transient"

#region Cleaning old file locations

find ${ZSHCOM__basedir:?}/.(state|var)* -maxdepth 0 -type f -exec rm {} \;

#endregion

# Shared with python
export ZSHCOM__mf_dependencies_checked="$ZSHCOM__transient/.state_dependencies_checked"
export ZSHCOM__mf_update_dependencies="$ZSHCOM__transient/.state_update_dependencies"
export ZSHCOM__mf_trigger_resource="$ZSHCOM__transient/.state_trigger_resource"
export ZSHCOM__mf_trigger_update="$ZSHCOM__transient/.state_trigger_update"
export ZSHCOM__mf_repo_update_checked="$ZSHCOM__cache/.state_repo_update_checked"
export ZSHCOM__mf_repo_updated="$ZSHCOM__cache/.state_repo_updated"
export ZSHCOM__mf_init_data="$ZSHCOM__basedir/initData.json"

export ZSHCOM__mf_break_init="$ZSHCOM__basedir/.state_break_init"
export ZSHCOM__mf_init="$ZSHCOM__basedir/init.sh"