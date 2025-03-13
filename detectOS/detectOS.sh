#!/bin/zsh

export ZSHCOM__known_os=''
export ZSHCOM__pkg_install=''

SAVEIFS=$IFS
IFS=$'\n'
exports=($("${ZSHCOM_PYTHON:?}" "${ZSHCOM__basedir:?}/detectOS/detect_os.py"))
IFS=$SAVEIFS

for e in $exports; do
  if [[ "$e" =~ 'export '* ]]; then
    k=$(echo "$e" | sed -E 's/^export ([^=]+)=(.+)$/\1/' )
    v=$(echo "$e" | sed -E 's/^export ([^=]+)=(.+)$/\2/' )

    eval export $k="$v"
  fi
done