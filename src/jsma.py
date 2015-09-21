import sys
import glob
import time

import os
import subprocess32

if os.name == 'nt':
    import win32pdh
    import win32api
    import win32con


# ~~~~~~~~~
# Exit codes. All must be > 100. Cause codes < 100 are reserved by java applications ans shell scripts

CODE_NOT_MANAGED_ERROR = 0
CODE_BAD_ARGUMENTS = 100
CODE_BAD_APP_FILES = 110
CODE_CANT_KILL_APP = 120
CODE_APP_ALREADY_STARTED = 130
CODE_CANT_START_PROCESS = 160
CODE_CANT_START_INVALID_STDOUT = 161
CODE_CANT_START_PROCESS_TIMEOUT_DONE = 162
CODE_CANT_START_SIGNALS_ABOUT_ERROR_BUT_DOESNT_STOPS = 163
CODE_CANT_START_INVALID_STARTING_RESULT_STRING = 164
CODE_CANT_START_EXCEPTION_WHILE_WAITING_APP_DONE = 165
CODE_CANT_STOP_CAUSE_NO_APP = 170
CODE_CANT_STOP_CAUSE_STILL_RUN = 180
CODE_CANT_DELETE_PID_FILE = 190
CODE_CANT_DELETE_SPRING_PROFILE_FILE = 191


# ~~~~~~~~~
# Parameters

DEFAULT_SPRING_PROFILE = 'local'

# time duration (in seconds) to let application signals about successful start
DEFAULT_APP_START_TIMEOUT = 30

# time duration (in seconds) to let application finishes its work
DEFAULT_APP_STOP_TIMEOUT = 15


class Params:
    def __init__(self, spring_profile, start_timeout, stop_timeout, rem_args):
        self.profile = spring_profile
        self.start_timeout = start_timeout
        self.stop_timeout = stop_timeout
        self.args = rem_args


# ~~~~~~~~~
# Validate and parse arguments

def parse_arguments():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        remaining_args = sys.argv[2:]

        if cmd in ['start', 'stop', 'status']:
            min_args_count = {'start': 1, 'stop': 0, 'status': 0}
            if len(remaining_args) >= min_args_count.get(cmd):
                profile = DEFAULT_SPRING_PROFILE
                start_timeout = DEFAULT_APP_START_TIMEOUT
                stop_timeout = DEFAULT_APP_STOP_TIMEOUT

                for a in remaining_args:
                    if a.find('--%') == 0:
                        profile = a[3:]
                    if a.find('--start-timeout=') == 0:
                        start_timeout = int(a[16:])
                    if a.find('--stop-timeout=') == 0:
                        stop_timeout = int(a[15:])

                if '--%{}'.format(profile) in remaining_args:
                    remaining_args.remove('--%{}'.format(profile))
                if '--start-timeout={}'.format(start_timeout) in remaining_args:
                    remaining_args.remove('--start-timeout={}'.format(start_timeout))
                if '--stop-timeout={}'.format(stop_timeout) in remaining_args:
                    remaining_args.remove('--stop-timeout={}'.format(stop_timeout))

                return cmd, Params(profile, start_timeout, stop_timeout, remaining_args)

    print r""
    print r" Wrong using! Possible templates:"
    print r" - server start --%[spring_profile] [jvm_args]"
    print r" - server stop"
    print r" - server status"
    print r""
    sys.exit(CODE_BAD_ARGUMENTS)


# ~~~~~~~~~
# Files

def detect_application_jar(application_path):
    jars = filter(os.path.isfile, glob.glob(application_path + '/*.jar'))
    if len(jars) == 1:
        return jars[0]
    else:
        print "~ Cannot detect application jar. Jars: {}".format(jars)
        print "~"
        sys.exit(CODE_BAD_APP_FILES)


def detect_pid_file(application_path):
    return os.path.join(application_path, 'server.pid')


def detect_spring_profile_file(application_path):
    return os.path.join(application_path, 'spring.profile')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Java utils

def java_path():
    if 'JAVA_HOME' not in os.environ:
        return "java"
    else:
        return os.path.normpath("{}/bin/java".format(os.environ['JAVA_HOME']))


def java_cmd(app_jar, p):
    args = p.args[:] if p.args is not None else ['']
    args.append('-server')
    args.append('-Dfile.encoding=utf-8')
    args.append('-Dspring.profiles.active={}'.format(p.profile))

    return [java_path()] + args + ['-jar', app_jar]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# To resolve localization problems.
# From here: http://python.su/forum/topic/2599/
# and here: http://pyxr.sourceforge.net/PyXR/c/python24/lib/site-packages/win32/lib/win32pdhutil.py.html
counter_english_map = {}


def find_pdh_counter_localized_name(english_name, machine_name=None):
    if not counter_english_map:
        counter_reg_value = win32api.RegQueryValueEx(win32con.HKEY_PERFORMANCE_DATA, "Counter 009")
        counter_list = counter_reg_value[0]
        for i in range(0, len(counter_list) - 1, 2):
            try:
                counter_id = int(counter_list[i])
            except ValueError:
                continue
            counter_english_map[counter_list[i + 1].lower()] = counter_id
    return win32pdh.LookupPerfNameByIndex(machine_name, counter_english_map[english_name.lower()])


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions to work with processes

# ~~~~~~~~~
# Kill process by it's pid

def kill(pid):
    if os.name == 'nt':
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(1, False, int(pid))
        if not ctypes.windll.kernel32.TerminateProcess(handle, 0):
            print "~ Cannot kill the process with pid {} (ERROR {})".format(pid, ctypes.windll.kernel32.GetLastError())
            print "~ "
            sys.exit(CODE_CANT_KILL_APP)
    else:
        try:
            os.kill(int(pid), 15)
        except OSError:
            print "~ Server was not running (Process id {} not found)".format(pid)
            print "~"
            sys.exit(CODE_CANT_KILL_APP)


# ~~~~~~~~~
# Check is process running

def process_running(pid):
    if os.name == 'nt':
        try:
            return process_running_nt(pid)
        except:
            return False
    else:
        try:
            os.kill(int(pid), 0)
            return True
        except OSError:
            return False


# loosely based on http://code.activestate.com/recipes/303339/
# and edited with: find_pdh_counter_localized_name()
def process_list_nt():
    process = find_pdh_counter_localized_name("Process", None)
    counter = find_pdh_counter_localized_name("ID Process", None)

    # each instance is a process, you can have multiple processes w/same name
    junk, instances = win32pdh.EnumObjectItems(None, None, process, win32pdh.PERF_DETAIL_WIZARD)
    proc_ids = {}
    proc_dict = {}
    for instance in instances:
        if instance in proc_dict:
            proc_dict[instance] += 1
        else:
            proc_dict[instance] = 0
    for instance, max_instances in proc_dict.items():
        for inum in xrange(max_instances + 1):
            hq = win32pdh.OpenQuery()  # initializes the query handle
            path = win32pdh.MakeCounterPath((None, process, instance, None, inum, counter))
            counter_handle = win32pdh.AddCounter(hq, path)
            win32pdh.CollectQueryData(hq)  # collects data for the counter
            type_res, val = win32pdh.GetFormattedCounterValue(counter_handle, win32pdh.PDH_FMT_LONG)
            proc_ids[str(val)] = instance
            win32pdh.CloseQuery(hq)

    return proc_ids


def process_running_nt(pid):
    if process_list_nt().get(pid, "") != "":
        return True
    else:
        return False


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Commands

# ~~~~~~~~~
# Command: start

# magic strings to detect application signalization
MAGIC_STRING = "APP_START_RESULT: "
SUCCESSFUL_START = "STARTED"
FAILURE_START = "NOT STARTED"


# returns (Result, PID, Code)
def _start_app(app_start_command, file_path, application_parameters):
    with open(file_path, 'w') as sout_file:
        try:
            p = subprocess32.Popen(app_start_command, bufsize=0, stdout=sout_file, stderr=sout_file, env=os.environ)
        except OSError:
            print "~ Could not execute the java executable, please make sure the JAVA_HOME environment variable is " \
                  "set properly (the java executable should reside at JAVA_HOME/bin/java). "
            sys.exit(CODE_CANT_START_PROCESS)

        ts = time.time()
        while True:
            if time.time() - ts > application_parameters.start_timeout:
                print "~ Error! Timeout waiting process signals about start result"
                kill(p.pid)
                break

            with open(file_path, 'r') as log:
                possible_result = [l[len(MAGIC_STRING):] for l in log if l.startswith(MAGIC_STRING)]
                if len(possible_result) == 0:
                    time.sleep(0.1)
                    continue

                if possible_result[0].startswith(SUCCESSFUL_START):
                    return True, p.pid, None
                else:
                    print "~ Error! Application signals that it is not started"
                    break

    print "~ Waiting for process done"
    try:
        code = p.wait(timeout=application_parameters.stop_timeout)
        print "~ Return code: {}".format(code)
        print "~"
    except Exception as e:
        print "~ Error! Exception while waiting for application done: {}".format(repr(e))
        print "~"
        return False, None, CODE_CANT_START_EXCEPTION_WHILE_WAITING_APP_DONE

    return False, None, code


def start(application_path, application_parameters):
    application = detect_application_jar(application_path)
    pid_file = detect_pid_file(application_path)
    spring_profile_file = detect_spring_profile_file(application_path)

    # detect process can be started
    if os.path.exists(pid_file):
        pid = open(pid_file).readline().strip()
        if process_running(pid):
            print "~ Oops. Server from {} is already started (pid:{})! (or delete {})".format(
                application_path, pid, os.path.normpath(pid_file))
            print "~"
            sys.exit(CODE_APP_ALREADY_STARTED)
        else:
            print "~ removing pid file {} for not running pid {}".format(pid_file, pid)
            print "~"
            os.remove(pid_file)

    if os.path.exists(spring_profile_file):
        print "~ removing settings profile file {}".format(spring_profile_file)
        print "~"
        os.remove(spring_profile_file)

    # stdout log
    stdout_file = os.path.join(application_path, 'system.out')
    if os.path.exists(stdout_file):
        os.remove(stdout_file)

    cmd = java_cmd(application, application_parameters)
    res, pid, code = _start_app(cmd, stdout_file, application_parameters)

    if not res:
        sys.exit(code)

    # say all ok, save pid to file
    print "~ OK, Server: {}".format(os.path.basename(application))
    with open(os.path.join(application_path, 'server.pid'), 'w') as pid_fl:
        pid_fl.write(str(pid))
    with open(os.path.join(application_path, 'spring.profile'), 'w') as spring_profile_fl:
        if application_parameters.profile is not None:
            spring_profile_fl.write(application_parameters.profile)
    print "~ spring active profile is: {}".format(application_parameters.profile)
    print "~ pid is: {}".format(pid)
    print "~"


# ~~~~~~~~~
# Command: stop

def _wait_for_process_stop(pid, application_parameters):
    stop_timeout = time.time()
    while True:
        if not process_running(pid):
            return True
        if time.time() - stop_timeout > application_parameters.stop_timeout:
            return False
        time.sleep(0.1)


def stop(application_path, application_parameters):
    pid_file = detect_pid_file(application_path)
    if not os.path.exists(pid_file):
        print "~ Oops! Server is not started (server.pid not found)"
        print "~"
        sys.exit(CODE_CANT_STOP_CAUSE_NO_APP)

    pid = open(pid_file).readline().strip()
    print "~ Try to stop process with pid: {}".format(pid)

    kill(pid)

    is_stopped = _wait_for_process_stop(pid, application_parameters)
    if not is_stopped:
        print "~ Oops! Cant stop server"
        print "~"
        sys.exit(CODE_CANT_STOP_CAUSE_STILL_RUN)

    os.remove(pid_file)
    if os.path.exists(pid_file):
        print "~ Oops! Application was stopped but cant delete pid file: {}".format(pid_file)
        print "~"
        sys.exit(CODE_CANT_DELETE_PID_FILE)

    spring_profile_file = detect_spring_profile_file(application_path)
    if os.path.exists(spring_profile_file):
        os.remove(spring_profile_file)
        if os.path.exists(spring_profile_file):
            print "~ Oops! Application was stopped but cant delete spring profile file: {}".format(spring_profile_file)
            print "~"
            sys.exit(CODE_CANT_DELETE_SPRING_PROFILE_FILE)

    print "~ OK, stopped!"
    print "~"


# ~~~~~~~~~
# Command: status

def status(application_path):
    pid_file = detect_pid_file(application_path)
    if not os.path.exists(pid_file):
        print "~ No pid file in folder: {}".format(os.getcwd())
        print "~ Application is not running"
        print "~"
        return

    pid = open(pid_file).readline().strip()
    if not os.path.exists("/proc/{}".format(pid)):
        print "~ Pid file found but no linked process. pid: {}".format(pid)
        print "~ Application is not running"
        print "~"
        return

    print "~ Pid file found and found linked process. pid: {}".format(pid)

    spring_profile_file = detect_spring_profile_file(application_path)
    if not os.path.exists(spring_profile_file):
        print "~ No active spring profile file"
    else:
        profile = open(spring_profile_file).readline().strip()
        print "~ Active spring profile file found. profile: {}".format(profile)

    print "~ Application is running"
    print "~"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Main

try:
    command, params = parse_arguments()
    java_app_path = os.getcwd()

    if command == 'start':
        start(java_app_path, params)
    if command == 'stop':
        stop(java_app_path, params)
    if command == 'status':
        status(java_app_path)

except KeyboardInterrupt:
    print '~ ...'
    sys.exit(CODE_NOT_MANAGED_ERROR)
