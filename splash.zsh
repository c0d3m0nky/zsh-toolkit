# shellcheck source=./init.zsh


if [[ $ZSHCOM_HIDE_SPLASH != true ]]; then

  if [[ -n "$ZSHCOM__banner_cmd" ]]; then
    $ZSHCOM__banner_cmd
  else
    sf="${ZSHCOM__basedir:?}/banners/${ZSHCOM__banner:?}.zsh"

    if [[ ! -f "$sf" ]]; then
      sf="$ZSHCOM__basedir/banners/default.zsh"
    fi

    if [[ -f $HOME/.ztk-banner ]]
    then
      echo ''
      zsh -c "$(cat "$HOME/.ztk-banner")"
    else
      echo ''
      zsh -c "$(cat "$sf")"
    fi
  fi

  echo "${zcOFF:?}"

  if [[ $ZSHCOM_HIDE_SPLASH_INFO != true ]]
  then
    {
      echo -e "  ${zcGreen:?}ztk-update${zcOFF}~Updates zsh-toolkit"
      echo -e "  ${zcGreen:?}ztk-debug${zcOFF}~Show debug info"
    }  | column -t -s '~' -R 1 -o ': ';
    echo ''
  fi
fi
