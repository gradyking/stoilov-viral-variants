#!/bin/bash
# used by Cromwell to find the singularity container that corresponds to the Docker container request

docker="$1"
cwd="$2"
docker_cwd="$3"
job_shell="$4"
docker_script="$5"

# If no docker image is specified, run locally
if [[ -z "${docker}" ]]; then
  echo "No docker image specified — running locally."
  bash "${job_shell}" "${docker_script}"
  exit $?
fi

# manipulate quay.io/broadinstitute/viral-core@sha256:1f1b274195ac4f4c7b08c462757b3f124c3cc53f279ce99b938c520a0c5871f3 into viral-core
docker_base="$(basename "${docker%%[@:]*}")"

# find project folder
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

if [[ ! -f "$SCRIPT_DIR/broadDockers/${docker_base}.sif" ]]; then
  echo "ERROR: Singularity image $SCRIPT_DIR/broadDockers/${docker_base}.sif not found."
  exit 1
fi

singularity exec --containall --bind "${cwd}:${docker_cwd}" "$SCRIPT_DIR/broadDockers/${docker_base}.sif" "${job_shell}" "${docker_script}"
