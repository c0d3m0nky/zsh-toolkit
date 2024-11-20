#!/bin/zsh
# shellcheck disable=SC2034

mf_transient=''

if [[ -n "${ZSHCOM_TRANSIENT}" &&  -d $ZSHCOM_TRANSIENT ]]
then
  mf_transient=$ZSHCOM_TRANSIENT
elif [[ -n "${XDG_RUNTIME_DIR}" &&  -d $XDG_RUNTIME_DIR ]]
then
  mf_transient=$XDG_RUNTIME_DIR/zsh_toolkit
fi

if [[ -z "${mf_transient}" ]]
then
  if [[ ${ZSHCOM__known_os:?} == 'win' ]]
  then
    mf_transient='/tmp/zsh_toolkit'
  elif [[ -d "/run/user/$UID" ]]
  then
    mf_transient="/run/user/$UID/zsh_toolkit"
  fi
  elif [[ -d /dev/shm ]]
  then
    mf_transient='/dev/shm/zsh_toolkit'
  fi
fi

if [[ -n "${mf_transient}" && -d $(dirname "$mf_transient") ]]
then
  export ZSHCOM__transient=$mf_transient
else
  echo "!!! Transient files not supported, set ZSHCOM_TRANSIENT in .zshrc"
fi


mkdir -p "$mf_transient"

#region Cleaning old file locations

clean_files=(
  "${ZSHCOM__basedir:?}/.state_dependencies_checked"
  "$ZSHCOM__basedir/.state_update_dependencies"
  "$ZSHCOM__basedir/.state_trigger_resource"
  "$ZSHCOM__basedir/.state_trigger_update"
)

for f in "${clean_files[@]}"
do
  if [ -f "${f}" ]
  then
    rm "$f"
  fi
done

#endregion

# Shared with python
export ZSHCOM__mf_dependencies_checked="$ZSHCOM__transient/.state_dependencies_checked"
export ZSHCOM__mf_update_dependencies="$ZSHCOM__transient/.state_update_dependencies"
export ZSHCOM__mf_trigger_resource="$ZSHCOM__transient/.state_trigger_resource"
export ZSHCOM__mf_trigger_update="$ZSHCOM__transient/.state_trigger_update"
export ZSHCOM__mf_repo_update_checked="$ZSHCOM__basedir/.state_repo_update_checked"
export ZSHCOM__mf_repo_updated="$ZSHCOM__basedir/.state_repo_updated"
export ZSHCOM__mf_init_data="$ZSHCOM__basedir/initData.json"

export ZSHCOM__mf_break_init="$ZSHCOM__basedir/.state_break_init"
export ZSHCOM__mf_init="$ZSHCOM__basedir/init.sh"