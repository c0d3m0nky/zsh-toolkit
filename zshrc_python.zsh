#!/usr/bin/env zsh

if [[ -z $PYTHONSTARTUP ]]; then
  export PYTHONSTARTUP=$HOME/.pythonrc.py
  if [[ ! -f "$PYTHONSTARTUP" ]]; then
    echo '
from pathlib import Path
' > "$PYTHONSTARTUP";
  fi
fi

alias pip-freeze-top='pip list --not-required --format freeze'
