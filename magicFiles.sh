#!/bin/zsh
# shellcheck disable=SC2034

# Shared with python
# shellcheck disable=SC2154
mf_dependencies_checked="$ZSHCOM__basedir/.state_dependencies_checked"
mf_update_dependencies="$ZSHCOM__basedir/.state_update_dependencies"
mf_trigger_resource="$ZSHCOM__basedir/.state_trigger_resource"
mf_trigger_update="$ZSHCOM__basedir/.state_trigger_update"
mf_repo_update_checked="$ZSHCOM__basedir/.state_repo_update_checked"
mf_repo_updated="$ZSHCOM__basedir/.state_repo_updated"
mf_init_data="$ZSHCOM__basedir/initData.json"


mf_break_init="$ZSHCOM__basedir/.state_break_init"
mf_init="$ZSHCOM__basedir/init.sh"