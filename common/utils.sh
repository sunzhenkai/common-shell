function FATAL() {
  echo "FATAL: $@"
  exit 1
}

function ERROR() {
  echo "ERROR: $@"
}

function WARN() {
  echo "WARN $@"
}

# tool::assert {expr} {message}
function tool::assert() {
  local expr=$1
  local message=$2
  if ! eval "[[ $expr ]]"; then
    FATAL "assert failed. [expr=\"$expr\", message=$message]"
  fi
}

tool::get_current_script_path() {
  local SOURCE DIR
  SOURCE="${BASH_SOURCE[-1]:-$0}"
  while [ -L "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
  done
  echo "$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)/$(basename "$SOURCE")"
}

tool::get_script_path() {
  usage="tool::get_script_path {script}"
  local SOURCE DIR
  SOURCE="${BASH_SOURCE:-$0}"
  while [ -L "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
  done
  echo "$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
}

function tool::is_same_file() {
  if ! command -v vim >/dev/null 2>&1; then
    echo 'program md5sum not exits'
    return 1
  fi
  if [ -e "$1" -a -e "$2" ]; then
    r1=$(md5sum "$1" | awk '{print $1}')
    r2=$(md5sum "$2" | awk '{print $1}')
    if [ $r1 = $r2 ]; then
      return 0
    else
      return 1
    fi
  else
    return 1
  fi
}

# package tool
function tool::os_type() {
  local os='unkown'
  if [[ "$OSTYPE" == "linux-gnu" ]]; then
    os='linux'
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    os='darwin'
  fi
  echo ${os}
}

function tool::cpu_arch() {
  echo $(uname -m)
}

function tool::cpu_arch_alias() {
  declare -A CPU_ARCH_ALIAS=(
    ["x86_64"]=amd64
  )
  als=${CPU_ARCH_ALIAS["$1"]}
  if [[ -z "$als" ]]; then
    echo "$1"
  else
    echo "$als"
  fi
}

# tool::append_if_not_exists {file} {text}
function tool::append_if_not_exists() {
  (! grep -q "$2" $1) && echo "append [ $2 ] into ${1}" && echo "$2" >>$1
}

# tool::append_to_profiles {text}
function tool::append_to_profiles() {
  profiles='.bashrc .bash_profile .zshrc'
  for i in $profiles; do
    [ -e "$HOME/$i" ] && echo "" >>"$HOME/$i" && tool::append_if_not_exists "$HOME/$i" "$1"
  done
}

# git
# tool::get_tag_version {default}
function tool::get_tag_version() {
  local tag_reversion=$1
  if [[ "X$tag_reversion" == "X" ]]; then
    tag_reversion=$(git describe --exact-match --tags 2>/dev/null || git rev-parse --short HEAD)
  fi
  echo "$tag_reversion"
}
