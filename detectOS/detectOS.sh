#!/bin/zsh

export ZSHCOM__known_os=''
export ZSHCOM__pkg_install=''

_trace "Running detect_os.py"
while read -r e; do
if [[ "$e" =~ 'export '* ]]; then
    k=$(echo "$e" | sed -E 's/^export ([^=]+)=(.+)$/\1/' )
    v=$(echo "$e" | sed -E 's/^export ([^=]+)=(.+)$/\2/' )

    # shellcheck disable=SC2086
    eval export $k="$v"
    _trace "$k=$v"
  fi
done < <("${ZSHCOM_PYTHON:?}" "${ZSHCOM__basedir:?}/detectOS/detect_os.py")