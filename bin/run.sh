# **********
# Attention!
# Must be execute by 'source' command instead of 'sh' or 'bash' commands.
#
# You cannot run it directly - no need to add Shebang line.
# **********

# Description.
# This is script to run Python app in virtualenv.
#
# Script want environment variables:
#  * PYTHON_APP_DIR
#  * PYTHON_EXECUTABLE_FILE
#  * PYTHON_REQUIREMENTS_FILE
#  * TARGET_APP_DIR
#  * ACTIONS_LOGS_DIR (optional)


# Define log_info function if not defined (by log.sh script)
if [ ! "$(type -t log_info)" == "function" ]; then
    function log_info () {
        echo "$@"
    }
fi

# Define log_warn function if not defined (by log.sh script)
if [ ! "$(type -t log_warn)" == "function" ]; then
    function log_warn () {
        log_info "$@"
    }
fi


# Use function - to use local keyword for variables and not produce side effects
function exec_app_in_virtualenv () {

# Exit codes
# must be >= 50, cause codes [0, 50) are reserved by java applications
local ERR_CODE_NO_PYTHON_APP_DIR=50
local ERR_CODE_BAD_PYTHON_APP_DIR=51
local ERR_CODE_NO_PYTHON_EXECUTABLE_FILE=52
local ERR_CODE_BAD_PYTHON_EXECUTABLE_FILE=53
local ERR_CODE_NO_PYTHON_REQUIREMENTS_FILE=54
local ERR_CODE_BAD_PYTHON_REQUIREMENTS_FILE=55
local ERR_CODE_NO_TARGET_APP_DIR=56
local ERR_CODE_BAD_TARGET_APP_DIR=57
local ERR_CODE_VIRTUALENV=58
local ERR_CODE_VIRTUALENV_ENTER=59
local ERR_CODE_REQUIREMENTS=60


log_info
log_info "---------- EXECUTE SCRIPT IN VIRTUALENV - START"
local FINAL_MESSAGE="---------- EXECUTE SCRIPT IN VIRTUALENV - STOP"

# -----
# Checking required environment variables
# -----
# for resolving relative paths use "$(readlink -m ${SOME})": http://stackoverflow.com/questions/6643853


# Define local variables (only for IDEA editor tips)
local PYTHON_DIR=""
local EXECUTABLE=""
local REQUIREMENTS=""
local APP_DIR=""
local LOGS_DIR=""


if [ -n "${PYTHON_APP_DIR+1}" ]; then
    PYTHON_DIR="$(readlink -m ${PYTHON_APP_DIR})"
else
    log_warn "[run.sh] [Error] No environment variable PYTHON_APP_DIR"
    return ${ERR_CODE_NO_PYTHON_APP_DIR}
fi

if [ ! -d ${PYTHON_DIR} ]; then
    log_warn "[run.sh] [Error] No dir of PYTHON_APP_DIR: ${PYTHON_DIR}"
    return ${ERR_CODE_BAD_PYTHON_APP_DIR}
fi

if [ -n "${PYTHON_EXECUTABLE_FILE+1}" ]; then
    EXECUTABLE="$(readlink -m ${PYTHON_EXECUTABLE_FILE})"
else
    log_warn "[run.sh] [Error] No environment variable PYTHON_EXECUTABLE_FILE"
    return ${ERR_CODE_NO_PYTHON_EXECUTABLE_FILE}
fi

if [ ! -f ${EXECUTABLE} ]; then
    log_warn "[run.sh] [Error] No file of EXECUTABLE_FILE: ${EXECUTABLE}"
    return ${ERR_CODE_BAD_PYTHON_EXECUTABLE_FILE}
fi

if [ -n "${PYTHON_REQUIREMENTS_FILE+1}" ]; then
    REQUIREMENTS="$(readlink -m ${PYTHON_REQUIREMENTS_FILE})"
else
    log_warn "[run.sh] [Error] No environment variable PYTHON_REQUIREMENTS_FILE"
    return ${ERR_CODE_NO_PYTHON_REQUIREMENTS_FILE}
fi

if [ ! -f ${REQUIREMENTS} ]; then
    log_warn "[run.sh] [Error] No file of PYTHON_REQUIREMENTS_FILE: ${REQUIREMENTS}"
    return ${ERR_CODE_BAD_PYTHON_REQUIREMENTS_FILE}
fi

if [ -n "${TARGET_APP_DIR+1}" ]; then
    APP_DIR="$(readlink -m ${TARGET_APP_DIR})"
else
    log_warn "[run.sh] [Error] No environment variable TARGET_APP_DIR"
    return ${ERR_CODE_NO_TARGET_APP_DIR}
fi

if [ ! -d ${APP_DIR} ]; then
    log_warn "[run.sh] [Error] No dir of PYTHON_APP_DIR: ${PYTHON_DIR}"
    return ${ERR_CODE_BAD_TARGET_APP_DIR}
fi

if [ -n "${ACTIONS_LOGS_DIR+1}" ]; then
    LOGS_DIR="$(readlink -m ${ACTIONS_LOGS_DIR})"
else
    LOGS_DIR="${APP_DIR}"
fi


log_info "Detect Python app directory: ${PYTHON_DIR}"
log_info "Detect Python executable: ${EXECUTABLE}"
log_info "Detect Python requirements: ${REQUIREMENTS}"
log_info "Detect app directory: ${APP_DIR}"
log_info "Detect logs directory: ${LOGS_DIR}"
log_info "~"

local CALLER_DIR="`pwd`"
cd ${PYTHON_DIR}


# -----
# Creating virtual environment
# -----

local VENV_DIR=${PYTHON_DIR}/.venv

if [ ! -d "${VENV_DIR}" ]; then
    log_info "Installing local virtual environment..."
    local VIRTUALENV_LOG=${LOGS_DIR}/virtualenv.log
    virtualenv .venv &> ${VIRTUALENV_LOG}
    local ENVERROR=$?

    if [ ${ENVERROR} -ne 0 ]; then
        log_warn "  Error. Details in ${VIRTUALENV_LOG}"
        log_info ${FINAL_MESSAGE}
        log_info

        cd ${CALLER_DIR}
        return ${ERR_CODE_VIRTUALENV}
    else
        log_info "  Done"
        rm ${VIRTUALENV_LOG}
    fi
else
    log_info "Local virtual environment detected in ${VENV_DIR}"
fi


# -----
# Enter into virtual environment
# -----

log_info "Enter into local virtual environment"
source ${VENV_DIR}/bin/activate

local PYTHON_EXECUTABLE_EXPECTED=${VENV_DIR}/bin/python
local PYTHON_EXECUTABLE_ACTUAL=`which python`
if [ ! "${PYTHON_EXECUTABLE_ACTUAL}" = "${PYTHON_EXECUTABLE_EXPECTED}" ]; then
    log_warn "  Error. python links to [${PYTHON_EXECUTABLE_ACTUAL}] but expect [${PYTHON_EXECUTABLE_EXPECTED}]"

    log_info "Exit from local virtual environment"
    deactivate

    log_info ${FINAL_MESSAGE}
    log_info

    cd ${CALLER_DIR}
    return ${ERR_CODE_VIRTUALENV_ENTER}
else
    log_info "  Done"
fi


# -----
# Resolving dependencies
# -----

log_info "Resolving dependencies..."
local REQUIREMENTS_LOG=${LOGS_DIR}/requirements.log
pip install -r ${REQUIREMENTS} &> ${REQUIREMENTS_LOG}
local REQSERROR=$?

if [ ${REQSERROR} -ne 0 ]; then
    log_warn "  Error. Details in ${REQUIREMENTS_LOG}"

    log_info "Exit from local virtual environment"
    deactivate

    log_info ${FINAL_MESSAGE}
    log_info

    cd ${CALLER_DIR}
    return ${ERR_CODE_REQUIREMENTS}
else
    log_info "  Done"
    rm ${REQUIREMENTS_LOG}
fi


# -----
# Running python app
# -----

log_info
log_info "========== RUNNING - START"

cd ${APP_DIR}
python ${EXECUTABLE} "$@"
local RUNERROR=$?

log_info "========== RUNNING - STOP"
log_info


# -----
# Finish execution
# -----

log_info "Exit from local virtual environment"
deactivate

cd ${CALLER_DIR}

log_info ${FINAL_MESSAGE}
log_info

if [ ${RUNERROR} -ne 0 ]; then
    return ${RUNERROR}
fi
}

exec_app_in_virtualenv "$@"
