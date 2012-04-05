#!/bin/bash
#
# hydra-agent Starts the hydra agent daemon
#
# chkconfig: 345 88 12
# description: starts the Hydra agent daemon
# processname: python

. /etc/init.d/functions

export PID_FILE=/var/run/hydra-agent.pid
export AGENT_BIN=/usr/bin/hydra-agent

start() {
    echo -n "Starting the Hydra Agent daemon: "
    $AGENT_BIN daemon
    echo
}

stop() {
    echo -n "Stopping the Hydra agent daemon: "
    kill $(cat ${PID_FILE})
    echo
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;

    restart|force-reload)
        stop
        start
        ;;
  *)
        echo "Usage: $0 {start|stop|restart|force-reload}" >&2
        exit 1
        ;;
esac

exit 0
