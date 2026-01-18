alias git-sizer="/mnt/c/git-sizer-1.3.0/linux/git-sizer"

function gitFetch() {
  git fetch origin "$1":"$1"
}

function gitDiff() {
  left=$1
  file=$2

  git difftool HEAD "$left" "$file"
}

function git-rename-fix() {
  mv $1 $2 && git mv $2 $1
}
