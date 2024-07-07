#!/bin/zsh

if [[ -d $HOME/.zsh-toolkit ]]
then
  vared -p 'zsh-toolkit is already installed, would you like to reinstall? (y/n): ' -c resp

  if [[ $resp != 'y' ]]; then
    exit 0
  fi

  echo Deleting $HOME/.zsh-toolkit
  rm -rf $HOME/.zsh-toolkit
fi

git clone git@github.com:c0d3m0nky/zsh-toolkit.git $HOME/.zsh-toolkit

zshrcCheck=$(grep '^ZSHCOM=' $HOME/.zshrc)

if [[ -z $zshrcCheck ]]
then
  cp $HOME/.zshrc $HOME/.zshrc.bak

  echo '\n\n### zsh-toolkit init' >> $HOME/.zshrc
  echo 'ZSHCOM="$HOME/.zsh-toolkit"' >> $HOME/.zshrc
  echo 'source $ZSHCOM/init.sh' >> $HOME/.zshrc
fi

ZSHCOM="$HOME/.zsh-toolkit"
source $ZSHCOM/init.sh