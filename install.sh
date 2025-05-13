#!/bin/zsh

if [[ -d $HOME/.zsh-toolkit ]]
then
  vared -p 'zsh-toolkit is already installed, would you like to reinstall? (y/n): ' -c resp

  if [[ ${resp:?} != 'y' ]]; then
    exit 0
  fi

  echo Deleting "$HOME/.zsh-toolkit"
  rm -rf "$HOME/.zsh-toolkit"
fi

git clone https://github.com/c0d3m0nky/zsh-toolkit.git "$HOME/.zsh-toolkit"

zshrcCheck=$(grep '^ZSHCOM=' "$HOME/.zshrc")

if [[ -z $zshrcCheck ]]
then
  cp "$HOME/.zshrc" "$HOME/.zshrc.bak"




  # shellcheck disable=SC2016
  {
    echo ''
    echo ''
    echo '### zsh-toolkit init';
    echo 'ZSHCOM="$HOME/.zsh-toolkit"';
    echo 'if [[ -f "$ZSHCOM/init.sh" ]]; then';
    echo '  localBin="$HOME/.local/bin"';
    echo '  if [[ ! $PATH =~ $localBin ]]; then export PATH="$localBin:$PATH"; fi';
    echo '  source $ZSHCOM/init.sh';
    echo 'else';
    echo '  echo "[zsh-toolkit]: missing $ZSHCOM/init.sh"';
    echo 'fi';
  } >> "$HOME/.zshrc"
fi

ZSHCOM="$HOME/.zsh-toolkit"
source "$ZSHCOM/init.sh"
