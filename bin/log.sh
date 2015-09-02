# **********
# Attention!
# Must be execute by 'source' command instead of 'sh' or 'bash' commands.
#
# You cannot run it directly - no need to add Shebang line.
# **********


# Description.
# Define global used do_log() function
# To let program output log, caller must pass "--VERBOSE" as first argument
#
# Must be called without passing any arguments - to let work with caller script arguments


if [ "$1" == "--VERBOSE" ]; then
    # 'shift' command: http://tldp.org/LDP/Bash-Beginners-Guide/html/sect_09_07.html
    shift

    function log_info () {
        echo "$@"
    }

    function log_warn () {
        echo "$@"
    }

else
    # empty functions: http://tldp.org/LDP/abs/html/functions.html
    function log_info () {
        :
    }

    function log_warn () {
            echo "!"
            echo "!   " "$@"
            echo "!"
    }
fi