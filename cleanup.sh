#!/bin/zsh


find "${ZSHCOM__basedir:?}/" -maxdepth 0 -type f  -name ".(state|var)*" -exec rm {} \;

if [[ -d "$HOME/.local/share/pipx/venvs/zsh-toolkit-py" ]]; then
  pipxPackUrl=$(cat "$HOME/.local/share/pipx/venvs/zsh-toolkit-py/pipx_metadata.json" | grep -Pi 'package_or_url' | sed -E 's/^\s+"package_or_url":\s+"([^"]+)".*?$/\1/')

  if [[ "$pipxPackUrl" =~ '/py/' ]]; then
    echo "Cleaning out old zsh_toolkit_py location, this may break but it's better than quietly failing"
    pipx uninstall zsh_toolkit_py
  fi
fi