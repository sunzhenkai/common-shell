BASE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source "$BASE/../../common/utils.sh"

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
  usage="docker::build {build-image} {source-path} {build-script} {dockerfile} {dest-image-tag}"
  local build_image=$1
  local source_path=$2
  local build_script=$3
  local dockerfile=$4
  local dest_image_tag=$5
  if [ ! $# -eq 5 ]; then
    FATAL "unexpected params count. [params($#): $@, usage: $usage]"
  fi

  local c_build_dir='/build'
  docker run --rm -t \
    -v "${source_path}:${c_build_dir}" \
    ${build_image} \
    bash -c "cd ${c_build_dir} && bash ${build_script}"
  tool::assert "$? -eq 0" "build failed"
}

docker::build 1 2 3 4 5
