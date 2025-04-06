get_script_abs_dir() {
  local SOURCE="${BASH_SOURCE[0]}"
  # fix source command
  if [ -z "$SOURCE" ]; then
    SOURCE=$1
  fi
  local DIR=$(cd -- "$(dirname -- "${SOURCE}")" &>/dev/null && pwd)
  echo "$DIR"
}

export COMMON_SHELL_DIR=$(get_script_abs_dir $0)
source $COMMON_SHELL_DIR/common/utils.sh
source $COMMON_SHELL_DIR/docker/builder/build.sh
