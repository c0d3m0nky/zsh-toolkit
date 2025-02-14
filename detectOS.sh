#!/bin/zsh

export ZSHCOM__known_os=''
export ZSHCOM__pkg_install=''

rel=$(cat /proc/cpuinfo | grep -Pi 'model\s+:\s+raspberry')

if [[ $rel != '' ]]
then
  export ZSHCOM__known_hw='pi'
fi

if [[ -f "/.dockerenv" ]]
then
  export ZSHCOM__known_hw='docker'
fi

if [[ -f /etc/os-release ]]
then
  rel=$(cat /etc/os-release | grep -Pi '^(id(_like)?)=arch$')

  if [[ $rel != '' ]]
  then
    export ZSHCOM__known_os='arch'
    export ZSHCOM__pkg_install='pacman -S'
  fi

  if [[ $ZSHCOM__known_os != '' ]]; then return; fi

  rel=$(cat /etc/os-release | grep -Pi '^(id(_like)?)=alpine$')

  if [[ $rel != '' ]]
  then
    export ZSHCOM__known_os='alpine'
    export ZSHCOM__pkg_install='apk add'
  fi

  if [[ $ZSHCOM__known_os != '' ]]; then return; fi

  rel=$(cat /etc/os-release | grep -Pi '^(id(_like)?)=debian$')

  if [[ $rel != '' ]]
  then
    export ZSHCOM__known_os='debian'
    export ZSHCOM__pkg_install='apt install'
  fi

  if [[ $ZSHCOM__known_os != '' ]]; then return; fi

  rel=$(cat /etc/os-release | grep -Pi '^(id(_like)?)="?slackware')

  if [[ $rel != '' && -f "/boot/license.txt" ]]
  then
    lic=$(cat "/boot/license.txt" | grep -Pi 'unraid')

    if [[ $lic != '' ]]
    then
      export ZSHCOM__known_os='unraid'
    fi
  fi
elif [[ "$OSTYPE" == 'msys' ]]
then
  export ZSHCOM__known_os='win'
fi
