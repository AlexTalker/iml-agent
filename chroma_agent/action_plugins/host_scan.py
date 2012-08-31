#
# ========================================================
# Copyright (c) 2012 Whamcloud, Inc.  All rights reserved.
# ========================================================


import datetime
import os
import socket

from chroma_agent.plugins import ActionPlugin
from chroma_agent.utils import list_capabilities
from chroma_agent import version


def host_properties(args = None):
    return {
        'time': datetime.datetime.utcnow().isoformat() + "Z",
        'nodename': os.uname()[1],
        'fqdn': socket.getfqdn(),
        'capabilities': list_capabilities(),
        'agent_version': version(),
    }


class HostScanPlugin(ActionPlugin):
    def register_commands(self, parser):
        p = parser.add_parser("host-properties")
        p.set_defaults(func=host_properties)
