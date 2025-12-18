source "$COMMON_SHELL_DIR/common/utils.sh"

# docker::ensure_container {image} {container_name}
function docker::ensure_container() {
  # 没有容器则创建容器，否则启动容器
  if ! (docker ps -a | grep "${2}"); then
    docker run -dt --name "${2}" -v /data -v /home "${1}" "${2}"
  else
    docker start "${2}"
  fi
}

function docker::build() {
  usage="docker::build {build-image} {source-path} {build-script} [{dockerfile} {dest-image-tag}]"
  local build_image=$1
  local source_path=$2
  local build_script=$3
  local dockerfile=$4
  local dest_image_tag=$5
  [[ $# -lt 3 ]] && ERROR "unexpected params count. \n\tparams($#): $@ \n\tusage: $usage" && return 5

  # build application
  local c_build_dir='/build'
  local env_args=""
  
  # 传递用户 ID 和组 ID 到容器中，用于设置文件权限
  if [ -n "$BUILD_UID" ]; then
    env_args="$env_args -e BUILD_UID=$BUILD_UID"
  fi
  if [ -n "$BUILD_GID" ]; then
    env_args="$env_args -e BUILD_GID=$BUILD_GID"
  fi
  
  docker run --rm -t \
    -v "${source_path}:${c_build_dir}" \
    ${env_args} \
    ${build_image} \
    bash --login -c "cd ${c_build_dir} && bash ${build_script}"
  [[ $? -ne 0 ]] && ERROR "build application failed" && return 5

  # [optional] build application image
  if [[ $# -eq 5 ]]; then
    pushd ${source_path} || exit 1
    docker build -f ${dockerfile} -t ${dest_image_tag} .
    [[ $? -eq 0 ]] && ERROR "build image failed" && return 5
    popd
  fi
}
