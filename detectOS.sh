#!/bin/zsh

export ZSHCOM__known_os=''
export ZSHCOM__pkg_install=''

if [[ ! -f /etc/os-release ]]; then exit 0; fi

rel=$(cat /etc/os-release | grep -Pi '^(id_like)=arch$')

if [[ $rel != '' ]]
then
  export ZSHCOM__known_os='arch'
  export ZSHCOM__pkg_install='pacman -S'
fi

if [[ $ZSHCOM__known_os != '' ]]; then exit 0; fi

rel=$(cat /etc/os-release | grep -Pi '^(id_like)=debian$')

if [[ $rel != '' ]]
then
  export ZSHCOM__known_os='debian'
  export ZSHCOM__pkg_install='apt install'
fi

if [[ $ZSHCOM__known_os != '' ]]; then exit 0; fi

rel=$(cat /etc/os-release | grep -Pi '^(id)=slackware$')

echo checking os-release

if [[ $rel != '' && -f "/boot/license.txt" ]]
then
  lic=$(cat "/boot/license.txt" | grep -Pi 'unraid')
  echo checking license
  if [[ $lic != '' ]]
  then
    echo setting ZSHCOM__known_os
    export ZSHCOM__known_os='unraid'
    echo $ZSHCOM__known_os
  fi
fi