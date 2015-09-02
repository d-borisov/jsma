#!/usr/bin/env bash

# Define variables for run.sh. Will be setted later
PYTHON_APP_DIR=""
PYTHON_EXECUTABLE_FILE=""
PYTHON_REQUIREMENTS_FILE=""
TARGET_APP_DIR=""


# Use function - to use local keyword for variables and not produce side effects
function run_jsma_in_virtual_environment () {

# -----
# Prepare environment variables
# -----

local CALLER_DIR="`pwd`"

# Get dir where is script file: http://stackoverflow.com/questions/59895
local SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# Convention-over-configuration: current file must be in [path_to_jda_project]/bin folder
cd ${SCRIPT_DIR}
cd ..

local WORKING_DIR="`pwd`"


# -----
# Define log functions depends on --VERBOSE argument
# -----

source ${SCRIPT_DIR}/log.sh


# -----
# Run JSMA app in vitrualenv
# -----

PYTHON_APP_DIR=${WORKING_DIR}
PYTHON_EXECUTABLE_FILE=${WORKING_DIR}/src/jsma.py
PYTHON_REQUIREMENTS_FILE=${WORKING_DIR}/requirements/requirements.txt
TARGET_APP_DIR=${CALLER_DIR}

source ${SCRIPT_DIR}/run.sh "$@"
EXECERROR=$?


# -----
# Finalization
# -----

cd ${CALLER_DIR}

if [ ${EXECERROR} -ne 0 ]; then
    return ${EXECERROR}
fi
}

run_jsma_in_virtual_environment "$@"