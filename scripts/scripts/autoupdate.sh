#!/bin/bash

# set -e

# BRANCH="master"
# ROOT_DIR="/home/owid/covid-19-data" #"$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../.. && pwd )"
# SCRIPTS_DIR=$ROOT_DIR/scripts


# # ENV VARS
# export OWID_COVID_PROJECT_DIR=${ROOT_DIR}
# export OWID_COVID_CONFIG=${OWID_COVID_PROJECT_DIR}/scripts/config.yaml
# export OWID_COVID_SECRETS=${OWID_COVID_PROJECT_DIR}/scripts/secrets.yaml
# export PATH=$PATH:/usr/local/bin/  # so geckodriver is correctly found


# # FUNCTIONS
# has_changed() {
#   git diff --name-only --exit-code $1 >/dev/null 2>&1
#   [ $? -ne 0 ]
# }

# has_changed_gzip() {
#   # Ignore the header because it includes the creation time
#   cmp --silent -i 8 $1 <(git show HEAD:$1)
#   [ $? -ne 0 ]
# }

# git_push() {
#   if [ -n "$(git status --porcelain)" ]; then
#     msg="data("$1"): automated update"
#     git add .
#     git commit -m "$msg"
#     git push origin $BRANCH
#   fi
# }

# run_python() {
#   (cd $SCRIPTS_DIR/scripts; python -c "$1")
# }

# # Move to the root directory
# cd $ROOT_DIR

# # Activate Python virtualenv
# source $SCRIPTS_DIR/venv/bin/activate

# # Make sure we have the latest commit.
# git reset --hard origin/$BRANCH && git pull origin $BRANCH


# =====================================================================
# Cases & Deaths

# Attempt to download JHU CSVs

# hour=$(date +%H)
# echo "Hour: $hour"  # Debugging output
# if [ "$hour" == "00" ] || [ "$hour" == "06" ] || [ "$hour" == "12" ] || [ "$hour" == "18" ]; then
#   echo "Generating Case/Death files..."
#   cowid --server casedeath generate
#   git_push "case-death"
# fi


# =====================================================================
# VAX ICER
# hour=$(date +%H)
# if [ $hour == 03 ] ; then
#   echo "Generating ICE vaccination data..."
#   cowid --server vax icer
# fi

# =====================================================================
# Hospital & ICU data

# hour=$(date +%H)
# if [ $hour == 05 ] || [ $hour == 17 ] ; then
#   # Download CSV
#   echo "Generating hospital & ICU export..."
#   cowid --server hosp generate
#   cowid --server hosp grapher-io
#   git_push "hosp"
# fi

# =====================================================================
# Vaccinations

# hour=$(date +%H)
# if [ $hour == 07 ] ; then
#   echo "Generating Vaccination (get, process, generate)..."
#   cowid --server vax get
#   cowid --server vax process generate
#   git_push "vax"
# fi

# =====================================================================
# Swedish Public Health Agency

# hour=$(date +%H)
# if [ $hour == 11 ] ; then
#   # Attempt to download data
#   cowid --server sweden get
#   if has_changed './scripts/input/sweden/sweden_deaths_per_day.csv'; then
#     echo "Generating Swedish Public Health Agency dataset..."
#     cowid --server sweden generate
#     git_push "sweden"
#   else
#     echo "Swedish Public Health Agency export is up to date"
#   fi
# fi

# =====================================================================
# UK subnational data
# hour=$(date +%H)
# if [ $hour == 13 ] ; then
#   # Download CSV
#   echo "Generating UK subnational export..."
#   cowid --server uk-nations generate
#   git_push "uk"
# fi

# =====================================================================
# Variants
# TODO: REMOVE
# hour=$(date +%H)
# if [ $hour == 19 ] ; then
#   echo "Generating CoVariants dataset..."
#   cowid --server variants generate
#   cowid --server variants grapher-io
#   git_push "variants"
# fi

# =====================================================================
# Excess Mortality
# hour=$(date +%H)
# if [ $hour == 21 ] ; then
#   echo "Generating XM dataset..."
#   cowid --server xm generate
#   git_push "xm"
# fi



# =====================================================================
# Megafile
# cowid --server megafile
# git_push "megafile"
