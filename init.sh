#!/bin/zsh

if [[ -z "$ZSHCOM" ]]
then
  echo "ZSHCOM is not set"
  exit 1
fi

ZSHCOM__basedir=$ZSHCOM
export ZSHCOM__basedir
export ZSHCOM__banner="default"

source "$ZSHCOM__basedir/magicFiles.sh"

# https://codehs.com/tutorial/ryan/add-color-with-ansi-in-javascript
export zcRed="\033[91m"
export zcOrange="\u001b[38;5;202m"
export zcYellow="\033[93m"
export zcGreen="\033[92m"
export zcBlue="\u001b[38;5;12m"
export zcCyan="\u001b[38;5;12m"
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

function _setVarCacehe() {
  varf="$ZSHCOM__basedir/.var_$1"

  eval "echo \$$1" > "$varf"
}

self=$(basename "$0")

_trace "Loading self: $self"

# ToDo: pip install (needs to be special for Arch distros

function _python_redirect() {
  funcStr="function ${1}() { python3 \$ZSHCOM__basedir/py/dependencies.py ${1} \$@; }"
  trace "eval $funcStr"
  eval "$funcStr"
}

function _loadSource() {
  d=$1

  for f in "$d"/zshrc_*
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

if [[ -z "$ZSHCOM__known_os" && -z "$ZSHCOM__known_hw" ]]
then
  _updateVar ZSHCOM__known_os
  _updateVar ZSHCOM__known_hw

  if [[ -z "$ZSHCOM__known_os" && -z "$ZSHCOM__known_hw" ]]
  then
    source "$ZSHCOM__basedir/detectOS.sh"
  fi

  _setVarCacehe ZSHCOM__known_os
  _setVarCacehe ZSHCOM__known_hw
fi

source "$ZSHCOM__basedir/update.sh"

if [[ ! -f "$mf_break_init" ]]
then
  _loadSource "$ZSHCOM__basedir"

  if [[ $ZSHCOM_NOPY != true ]]
  then
    python3 "$ZSHCOM__basedir/py/dependencies.py"
    if [[ -f "$mf_trigger_update" ]]
    then
      rm "$mf_trigger_update"
      ztk-update
      touch "$mf_break_init"
    fi
  fi

  if [[ ! -f "$mf_break_init" ]]
  then
    if [[ -d $ZSHCOM_POSTLOAD ]]
    then
      _loadSource "$ZSHCOM_POSTLOAD"
      # ToDo: handle python
    fi

    # choose banner

    if [[ $ZSHCOM__known_hw == 'pi' || $ZSHCOM__known_hw == 'docker' ]]; then ZSHCOM__banner=$ZSHCOM__known_hw; fi
    if [[ $ZSHCOM__known_os == 'unraid' || $ZSHCOM__known_os == 'debian' || $ZSHCOM__known_os == 'win' ]]; then ZSHCOM__banner=$ZSHCOM__known_os; fi

    source "$ZSHCOM__basedir/splash.sh"
  fi
fi

if [[ -f "$mf_break_init" ]]
then
  rm "$mf_break_init"
fi