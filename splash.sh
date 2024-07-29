# shellcheck source=./init.sh


if [[ $ZSHCOM_HIDE_SPLASH != true ]]
then
  sf="${ZSHCOM__basedir:?}/banners/${ZSHCOM__banner:?}.sh"

  if [[ ! -f "$sf" ]]
  then
    sf="$ZSHCOM__basedir/banners/default.sh"
  fi

  if [[ -f $HOME/.ztk-banner ]]
  then
    echo ''
    zsh -c "$(cat "$HOME/.ztk-banner")"
  else
    echo ''
    zsh -c "$(cat "$sf")"
  fi

  echo "${zcOFF:?}"

  if [[ $ZSHCOM_HIDE_SPLASH_INFO != true ]]
  then
    echo -e "${zcGreen:?}ztk-update${zcOFF} : Updates zsh-toolkit
  "
  fi
fi
