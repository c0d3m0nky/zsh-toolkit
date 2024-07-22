#!/bin/zsh

ZSHCOM__basedir=$(dirname "$0")
export ZSHCOM__basedir
export ZSHCOM__banner="default"

# https://codehs.com/tutorial/ryan/add-color-with-ansi-in-javascript
export zcRed="\033[91m"
export zcOrange="\u001b[38;5;202m"
export zcYellow="\033[93m"
export zcGreen="\033[92m"
export zcBlue="\u001b[38;5;12m"
export zcIndigo="\u001b[38;5;92m"
export zcViolet="\u001b[38;5;201m"
export zcOFF="\033[0m"

function _trace() {
  if [[ $ZSHCOM_TRACE == 'true' ]]
  then
    echo "$@";
  fi
}

function _updateVar() {
  varf="$ZSHCOM__basedir/.var_$1"
  varv=$(cat "$varf" 2>/dev/null || echo '~!~')

  if [[ "$varv" != '~!~' ]]
  then
    eval $1=$varv
    rm $varf
  fi
}

self=$(basename "$0")

_trace "Loading self: $self"

function detectOS() {
  export ZSHCOM__known_os=''
  export ZSHCOM__pkg_install=''

  if [[ ! -f /etc/os-release ]]; then return; fi

  rel=$(cat /proc/cpuinfo | grep -Pi 'model\s+:\s+raspberry')

  if [[ $rel != '' ]]
  then
    export ZSHCOM__known_hw='pi'
  fi

  if [[ -f "/.dockerenv" ]]
  then
    export ZSHCOM__known_hw='docker'
  fi

  rel=$(cat /etc/os-release | grep -Pi '^(id_like)=arch$')

  if [[ $rel != '' ]]
  then
    export ZSHCOM__known_os='arch'
    export ZSHCOM__pkg_install='pacman -S'
  fi

  if [[ $ZSHCOM__known_os != '' ]]; then return; fi

  rel=$(cat /etc/os-release | grep -Pi '^(id_like)=debian$')

  if [[ $rel != '' ]]
  then
    export ZSHCOM__known_os='debian'
    export ZSHCOM__pkg_install='apt install'
  fi

  if [[ $ZSHCOM__known_os != '' ]]; then return; fi

  rel=$(cat /etc/os-release | grep -Pi '^(id)=slackware$')

  if [[ $rel != '' && -f "/boot/license.txt" ]]
  then
    lic=$(cat "/boot/license.txt" | grep -Pi 'unraid')

    if [[ $lic != '' ]]
    then
      export ZSHCOM__known_os='unraid'
    fi
  fi
}

detectOS

# ToDo: include total
alias duh="du -hs */ | sort -h"
alias listDirs="find ./ -type d"
# shellcheck disable=SC2142
alias whatsmyip="host myip.opendns.com resolver1.opendns.com | ack 'myip.opendns.com has address ([\d.]+)' --output '\$1'"
alias whatsmyip-curl="curl checkip.amazonaws.com"
alias clip="tee >(xclip -r -selection clipboard)"
alias popout='upd=$(dirname $(pwd)); while [[ ! -d "$upd" ]]; do upd=$(dirname "$upd"); done; cd "$upd"'

# ToDo: pip install (needs to be special for Arch distros

function _python_redirect() {
  funcStr="function ${1}() { python3 \$ZSHCOM__basedir/py/common.py ${1} \$@; }"
  trace "eval $funcStr"
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
  python3 "$ZSHCOM__basedir/py/common.py"
fi

if [[ -d $ZSHCOM_POSTLOAD ]]
then
  _loadSource "$ZSHCOM_POSTLOAD"
  # ToDo: handle python
fi

function _splash() {
  sf="$ZSHCOM__basedir/banners/${ZSHCOM__banner}.sh"

  if [[ ! -f "$sf" ]]
  then
    sf="$ZSHCOM__basedir/banners/default.sh"
  fi

  if [[ -f $HOME/.ztk-banner ]]
  then
    zsh -c "$(cat "$HOME/.ztk-banner")"
  else
    zsh -c "$(cat "$sf")"
  fi

  print $zcOFF

  if [[ $ZSHCOM_HIDE_SPLASH_INFO != true ]]
  then
    echo -e "${zcGreen}ztk-update${zcOFF} : Updates zsh-toolkit
  "
  fi

}

_updateVar ZSHCOM__known_os
_updateVar ZSHCOM__banner
_updateVar ZSHCOM__known_hw

# choose banner

if [[ $ZSHCOM__known_hw == 'pi' || $ZSHCOM__known_hw == 'docker' ]]; then ZSHCOM__banner=$ZSHCOM__known_hw; fi
if [[ $ZSHCOM__known_os == 'unraid' || $ZSHCOM__known_os == 'debian' ]]; then ZSHCOM__banner=$ZSHCOM__known_os; fi

if [[ $ZSHCOM_HIDE_SPLASH != true ]]
then
  _splash
fi
