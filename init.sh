export ZSHCOM__basedir=$(dirname "$0")
self=$(basename "$0")

# echo Loading self: $self

# ToDo: include total
alias duh="du -hs */ | sort -h"
#alias nvtop="nvidia-smi -l 1"
#alias popShop="io.elementary.appcenter"
alias listDirs="find ./ -type d"
# shellcheck disable=SC2142
alias whatsmyip="host myip.opendns.com resolver1.opendns.com | ack 'myip.opendns.com has address ([\d.]+)' --output '\$1'"
alias whatsmyip-curl="curl checkip.amazonaws.com"
alias clip="tee >(xclip -r -selection clipboard)"

# ToDo: pip install (needs to be special for Arch distros

function _trace() {
  if [[ $ZSHCOM_TRACE == 'true' ]]
  then
    echo "$@";
  fi
}

function _python_redirect() {
  funcStr="function ${1}() { python3 \$ZSHCOM__basedir/py/common.py ${1} \$@; }"
  #echo "eval $funcStr"
  eval "$funcStr"
}

function _loadSource() {
  d=$1

  for f in $d/zshrc_*
  do
    _trace "$d - $f"
    if [[ ! $f == *.py ]]
    then
      _trace "Loading source $f"
      # shellcheck disable=SC1090
      source "$f"
    fi
  done
}

if [[ -d $ZSHCOM_PRELOAD ]]
then
  _loadSource "$ZSHCOM_PRELOAD"
  # ToDo: handle python
fi

_loadSource "$ZSHCOM__basedir"

# ! ToDo: check for rclone
alias rmv="rclone move -P --ignore-existing"

if ! command -v json_pp &> /dev/null
then 
  alias json_pp='python3 -m json.tool'
fi

if ! command -v xml_pp &> /dev/null
then
  if command -v xmllint &> /dev/null
  then
    alias xml_pp="xmllint --format -"
  else
    echo No xml pretty printer
  fi
fi

if [[ -z $ZSHCOM_DSH_USEZSH ]]; then ZSHCOM_DSH_USEZSH=''; fi

dockerShell() {
	if [[ $ZSHCOM_DSH_USEZSH == *${1}* ]]; then
		dockerZsh $1
	else
		docker exec -it $1 bash
	fi
}

perfwatch() {
	# shellcheck disable=SC2016
	sensors | ack -i '^(CPU|MB) Temp:\s+([\+\-\d.]+°[CF])' --output '$1:\t$2'
	echo ''
	echo ''
	# shellcheck disable=SC2016
	(cat /proc/cpuinfo | ack "^([c]pu MHz|processor)\s+:\s(.+)$" --output '$2') | ack '(\d+) (\d)(\d+)\.\d+ (\d+) (\d)(\d+)\.\d+ ' --output '$1\t$2.$3  $5.$6\t$4'
}

dockerZsh() {
	docker exec -it "$1" /bin/zsh
}

function pip-install-save { 
    pip install "$1" && pip freeze | grep "$1" >> requirements.txt
}

# ToDo: check if top level is single dir
un7zipall() {
	for i in *.7z; do 7za x "$i" -o${i%%.7z}; done
}

unzipall() {
	for i in *.zip; do unzip "$i" -d "${i%%.zip}"; done
}

unrarall() {
	for i in *.rar; do unrar x "$i" "${i%%.rar}/"; done
}

function set_title() {
  echo -e "\033]0;$1\007";
}

# ToDo: exclude ack's pid
function psack () {
  ps aux | ack -v '/usr/bin/ack' | ack -i $1
}

function fack () {
  find ./ -type f | ack $1
}

function findWithExtension() {
  badImg='\.(jpg_.+|r\d+|me-downloaders|torrent)$'

  if [[ $1 == '-bimg' ]]
  then
    #echo "find ./ -type f | ack -i \"${badImg}\""
    find ./ -type f | ack -i "${badImg}"
    return
  fi

  if [[ $1 == '-empty' ]]
   then
     find ./ -type f | ack -i "/[^./]+$"
     return
   fi
    

  rx='\.('

  # shellcheck disable=SC2068
  for a in $@
  do
    if [[ $rx != '\.(' ]]
    then
      rx="${rx}|"
    fi
    rx="${rx}${a}"
  done

  rx="${rx})$"
  #echo "find ./ -type f | ack \"${rx}\""
  find ./ -type f | ack -i "${rx}"
}

function touchFiles() {
  rec=''
  root=$1

  if [[ "$*" == *"-r"* ]]
  then
      rec='-r'
  fi

  if [[ ! -d $root ]]
  then
    echo invalid path
    return
  fi

  if [[ $rec == '-r' ]]
  then
#    echo recurse
    find "$root" -type f -exec touch {} +
  else
#    echo top
    find "$root" -maxdepth 1  -type f -exec touch {} +
  fi
}

if [[ $ZSHCOM_NOPY != true ]]
then
  for f in $(python3 $ZSHCOM__basedir/py/common.py _funcs)
  do
    # echo "_python_redirect $f"
    _python_redirect "$f"
  done
fi

if [[ -d $ZSHCOM_POSTLOAD ]]
then
  _loadSource "$ZSHCOM_POSTLOAD"
  # ToDo: handle python
fi

echo Loaded "zsh-toolkit"
