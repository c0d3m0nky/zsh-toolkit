#!/bin/zsh


find "${ZSHCOM__basedir:?}/" -maxdepth 0 -type f  -name ".(state|var)*" -exec rm {} \;
