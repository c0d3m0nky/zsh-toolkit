#!/bin/zsh

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

_trace "Loading zsh-toolkit"

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

if [[ -n "$ZSHCOM" ]]; then
  if [[ -z "$ZSHCOM_PYTHON" ]]; then
    ZSHCOM_PYTHON=$(which python3.12)

    if [[ -z "$ZSHCOM_PYTHON" ]]
    then
      pyLibLoc="$(dirname "$(which python3)")"
      # shellcheck disable=SC2086
      # shellcheck disable=SC2016
      pyVers=$(find $pyLibLoc/python*.* -type f -exec basename {} \; | ack '^python\d\.\d+$' --output '$1' | sort -Vr)

      for p in $pyVers
      do
        # shellcheck disable=SC2086
        ZSHCOM_PYTHON=$(which python$p)
        if [[ -n $ZSHCOM_PYTHON ]]
        then
          break
        fi
      done
    fi

    _trace "ZSHCOM_PYTHON=$ZSHCOM_PYTHON"
  fi

  if [[ -z $(which "$ZSHCOM_PYTHON") ]]
  then
    # shellcheck disable=SC2028
    echo "Python command not found, install python 3.12+ and/or set ZSHCOM_PYTHON to it's command"
    touch "${ZSHCOM__mf_break_init:?}"
  else
    export ZSHCOM_PYTHON="$ZSHCOM_PYTHON"
  fi

  if [[ -n "$ZSHCOM_PYTHON" ]]; then
    # Load config
    _trace "config.py"
    while read -r e; do
    if [[ "$e" =~ 'export '* ]]; then
        k=$(echo "$e" | sed -E 's/^export ([^=]+)=(.+)$/\1/' )
        v=$(echo "$e" | sed -E 's/^export ([^=]+)=(.+)$/\2/' )

        # shellcheck disable=SC2086
        eval export $k="$v"
        _trace "$k=$v"
      else
        echo "$e"
      fi
    done < <("${ZSHCOM_PYTHON:?}" "${ZSHCOM:?}/zsh_toolkit_py/init.py" --source)

    # ToDo: Hopefully one day shellcheck will use this directive to check for assignment and avoid SC2154 everywhere https://github.com/koalaman/shellcheck/issues/2956
    # shellcheck source=cleanup.sh
    source "${ZSHCOM__basedir:?}/cleanup.sh"

    if [[ -d $ZSHCOM_PRELOAD ]]
    then
      _loadSource "$ZSHCOM_PRELOAD"
    fi

    if [[ ! -f "$ZSHCOM__mf_break_init" ]]
    then
      if [[ -n $(which rclone) ]]
      then
        export ZSHCOM__feat_rclone=true
      else
        export ZSHCOM__feat_rclone=false
      fi

      _loadSource "$ZSHCOM__basedir"
      source "$ZSHCOM__basedir/update.sh"

      _trace dependencies.py
      $ZSHCOM_PYTHON "$ZSHCOM__basedir/zsh_toolkit_py/dependencies.py"
      if [[ -f "${ZSHCOM__mf_trigger_update:?}" ]]
      then
        rm "$ZSHCOM__mf_trigger_update"
        ztk-update
        touch "$ZSHCOM__mf_break_init"
      fi

      if [[ ! -f "$ZSHCOM__mf_break_init" ]]
      then
        if [[ -d $ZSHCOM_POSTLOAD ]]
        then
          _loadSource "$ZSHCOM_POSTLOAD"
          # ToDo: handle python
        fi

        # choose banner

        if [[ -z "$ZSHCOM__banner" ]]; then
          if [[ -n $ZSHCOM__known_hw ]]; then
            if [[ $ZSHCOM__known_hw == 'pi' || $ZSHCOM__known_hw == 'docker' ]]; then ZSHCOM__banner=$ZSHCOM__known_hw; fi
          fi

          if [[ -n $ZSHCOM__known_os ]]; then
            if [[ $ZSHCOM__known_os == 'unraid' || $ZSHCOM__known_os == 'debian' || $ZSHCOM__known_os == 'win' ]]; then ZSHCOM__banner=$ZSHCOM__known_os; fi
          fi

          if [[ -z "$ZSHCOM__banner" ]]; then ZSHCOM__banner="default"; fi
        fi

        source "$ZSHCOM__basedir/splash.sh"
      fi
    fi

    if [[ -f "$ZSHCOM__mf_break_init" ]]
    then
      rm "$ZSHCOM__mf_break_init"
    fi
  fi
else
  echo "[zsh-toolkit] ZSHCOM not set"
fi