#!/bin/zsh

function ztk-update() {
  _ztk-update "$@"

    if [[ -f "${ZSHCOM__mf_repo_updated:?}" ]]
  then
    # Re-sourcing self to apply changes before calling post
    source "${ZSHCOM__basedir:?}/update.sh"
  fi

  if [[ -f "${ZSHCOM__mf_update_dependencies:?}" ]]
  then
    rm "$ZSHCOM__mf_update_dependencies"
    # Re-sourcing self to apply changes before calling post
    echo "Re-sourcing ${ZSHCOM__mf_init:?}"
    # shellcheck disable=SC1090
    source "$ZSHCOM__mf_init"
  fi
}

function _post_ztk-update() {
  rm "$ZSHCOM__mf_repo_updated"

  echo "Re-sourcing $ZSHCOM__mf_init"
  # shellcheck disable=SC1090
  source "$ZSHCOM__mf_init"
}

if [[ -f "$ZSHCOM__mf_repo_updated" ]]
then
  _post_ztk-update
fi