#!/bin/zsh

function ztk-update() {
  _ztk-update "$@"

  # shellcheck disable=SC2154
  if [[ -f "$mf_repo_updated" ]]
  then
    # Re-sourcing self to apply changes before calling post
    source "$ZSHCOM__basedir/update.sh"
  fi

  # shellcheck disable=SC2154
  if [[ -f "$mf_update_dependencies" ]]
  then
    rm "$mf_update_dependencies"
    # Re-sourcing self to apply changes before calling post
    echo "Re-sourcing $mf_init"
    # shellcheck disable=SC1090
    source "$mf_init"
  fi
}

function _post_ztk-update() {
  rm "$mf_repo_updated"
  echo "Re-sourcing $mf_init"
  # shellcheck disable=SC1090
  source "$mf_init"
  # shellcheck disable=SC2154
  touch "$mf_break_init"
}

if [[ -f "$mf_repo_updated" ]]
then
  _post_ztk-update
fi