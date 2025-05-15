#!/bin/zsh
autoload is-at-least

missing=()
dependencies=('ack' 'alias')

function cmdMissing() {
  if command -v $1 &> /dev/null; then
    return 1
  fi

  return 0
}

function addMissing() {
  missing+=($1);
}

for c in $dependencies; do
  if cmdMissing $c; then
    addMissing $c;
  fi
done

if cmdMissing python3.11 && cmdMissing python3.12; then
  if ! cmdMissing python3; then
    if ! is-at-least 3.11 "$(python3 --version)"; then
      addMissing 'python3.11+'
    fi
  fi
fi

if [[ -n $missing ]]; then
  echo 'Missing dependencies:';
  for d in $missing; do
    echo -e "  - $d";
  done
  exit 1
fi

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
    echo 'export PATH="$PATH:$HOME/.local/bin"';
    echo 'ZSHCOM="$HOME/.zsh-toolkit"';
    echo 'source $ZSHCOM/init.sh';
  } >> "$HOME/.zshrc"
fi

ZSHCOM="$HOME/.zsh-toolkit"
source "$ZSHCOM/init.sh"
