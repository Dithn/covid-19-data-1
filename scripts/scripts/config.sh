#!/bin/bash

set -e

BRANCH="master"
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../.. && pwd )"
SCRIPTS_DIR=$ROOT_DIR/scripts


# ENV VARS
export OWID_COVID_PROJECT_DIR=${ROOT_DIR}
export OWID_COVID_CONFIG=${OWID_COVID_PROJECT_DIR}/scripts/config.yaml
export OWID_COVID_SECRETS=${OWID_COVID_PROJECT_DIR}/scripts/secrets.yaml
export PATH=$PATH:/usr/local/bin/ 


# FUNCTIONS
has_changed() {
  git diff --name-only --exit-code $1 >/dev/null 2>&1
  [ $? -ne 0 ]
}

has_changed_gzip() {
  # Ignore the header because it includes the creation time
  cmp --silent -i 8 $1 <(git show HEAD:$1)
  [ $? -ne 0 ]
}

git_push() {
  if [ -n "$(git status --porcelain)" ]; then
    msg="data("$1"): automated update"
    git add .
    git commit -m "$msg"
    git push
  fi
}

run_python() {
  (cd $SCRIPTS_DIR/scripts; python -c "$1")
}

# Move to the root directory
cd $ROOT_DIR

# Activate Python virtualenv
source $SCRIPTS_DIR/venv/bin/activate