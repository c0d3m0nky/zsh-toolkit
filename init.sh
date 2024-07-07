#!/bin/zsh

export ZSHCOM__basedir=$(dirname "$0")
self=$(basename "$0")

# echo Loading self: $self

# ToDo: include total
alias duh="du -hs */ | sort -h"
#alias nvtop="nvidia-smi -l 1"
#alias popShop="io.elementary.appcenter"
alias listDirs="find ./ -type d"
# shellcheck disable=SC2142
alias whatsmyip="host myip.opendns.com resolver1.opendns.com | ack 'myip.opendns.com has address ([\d.]+)' --output '\$1'"
alias whatsmyip-curl="curl checkip.amazonaws.com"
alias clip="tee >(xclip -r -selection clipboard)"

# ToDo: pip install (needs to be special for Arch distros

function _trace() {
  if [[ $ZSHCOM_TRACE == 'true' ]]
  then
    echo "$@";
  fi
}

function _python_redirect() {
  funcStr="function ${1}() { python3 \$ZSHCOM__basedir/py/common.py ${1} \$@; }"
  #echo "eval $funcStr"
  eval "$funcStr"
}

function _loadSource() {
  d=$1

  for f in $d/zshrc_*
  do
    _trace "$d - $f"
    if [[ ! $f == *.py ]]
    then
      _trace "Loading source $f"
      # shellcheck disable=SC1090
      source "$f"
    fi
  done
}

if [[ -d $ZSHCOM_PRELOAD ]]
then
  _loadSource "$ZSHCOM_PRELOAD"
  # ToDo: handle python
fi

_loadSource "$ZSHCOM__basedir"

# ! ToDo: check for rclone
alias rmv="rclone move -P --ignore-existing"

if ! command -v json_pp &> /dev/null
then 
  alias json_pp='python3 -m json.tool'
fi

if ! command -v xml_pp &> /dev/null
then
  if command -v xmllint &> /dev/null
  then
    alias xml_pp="xmllint --format -"
  else
    echo No xml pretty printer
  fi
fi

if [[ $ZSHCOM_NOPY != true ]]
then
  python3 $ZSHCOM__basedir/py/common.py
fi

if [[ -d $ZSHCOM_POSTLOAD ]]
then
  _loadSource "$ZSHCOM_POSTLOAD"
  # ToDo: handle python
fi

echo Loaded "zsh-toolkit"
