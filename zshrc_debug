


function ztk-debug() {
  echo ''
  echo Vars
  echo ''

  # shellcheck disable=SC2016
  printenv | ack '^(ZSHCOM__(?!mf_)[^ =]+)=(.+)$' --output '$1~$2' | sort | column -t -s '~'

  echo ''
  echo Magic Files
  echo ''

  {
    # shellcheck disable=SC2016
    for mf in $(printenv | ack '^(ZSHCOM__mf_[^ =]+)=(.+)$' --output '$1~$2')
    do
      var=${mf%~*};
      path=${mf#*~};

      if [[ -f "$path" ]]
      then
        echo "${var}~${zcGreen:?}✓${zcOFF:?}~${path}"
      else
        echo "${var}~${zcRed:?}X${zcOFF}~${path}"
      fi
    done
  } | column -t -s '~';

  echo ''
  echo pipx list
  echo ''

  pipx list

  possibleIssues=()

  if [[ -z $ZSHCOM__known_os || -z $ZSHCOM__pkg_mgr ]]; then
    msg='OS detection failure'

    if [[ -z $ZSHCOM__known_os ]]; then
      msg="$msg\n\tZSHCOM__known_os not set"
    fi

    if [[ -z $ZSHCOM__pkg_mgr ]]; then
      msg="$msg\n\ZSHCOM__pkg_mgr not set"
    fi

    possibleIssues+=("$msg")
  fi

  if (( ${#possibleIssues[@]} > 0 )); then

    echo ''
    echo "${zcRed}!!!!! Possible Issues !!!!!${zcOFF}"
    echo ''

    # shellcheck disable=SC2128
    for e in $possibleIssues; do
      echo "$e"
    done

    echo ''
    echo "${zcRed}!!!!!${zcOFF}"
    echo ''
  fi
}



