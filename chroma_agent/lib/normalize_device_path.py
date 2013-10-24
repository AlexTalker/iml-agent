#
# INTEL CONFIDENTIAL
#
# Copyright 2013-2014 Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related
# to the source code ("Material") are owned by Intel Corporation or its
# suppliers or licensors. Title to the Material remains with Intel Corporation
# or its suppliers and licensors. The Material contains trade secrets and
# proprietary and confidential information of Intel or its suppliers and
# licensors. The Material is protected by worldwide copyright and trade secret
# laws and treaty provisions. No part of the Material may be used, copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be
# express and approved by Intel in writing.


import os
import glob
import re

MAPPERPATH = os.path.join('/dev', 'mapper')
DISKBYIDPATH = os.path.join('/dev', 'disk', 'by-id')

_normalize_device_table = {}


def normalized_device_path(device_path):
    _prime_normalized_paths()

    normalized_path = os.path.realpath(device_path)

    # This checks we have a completely normalized path, perhaps the stack means our current
    # normal path can actually be normalized further. So if the root to normalization takes multiple
    # steps this will deal with it
    # So if /dev/sdx normalizes to /dev/mmapper/special-device
    # but /dev/mmapper/special-device normalizes to /dev/md/mdraid1
    # /dev/sdx will normalize to /dev/md/mdraid1

    # As an additional measure to detect circular references such as A->B->C->A in
    # this case we don't know which is the normalized value so just drop out once
    # it repeats.
    visited = set()

    while (normalized_path not in visited) and (normalized_path in _normalize_device_table):
        visited.add(normalized_path)
        normalized_path = _normalize_device_table[normalized_path]

    return normalized_path


def find_normalized_end(device_path):
    _prime_normalized_paths()

    for key, value in _normalize_device_table.items():
        if value.endswith(device_path):
            return value

    raise KeyError("Device ending with %s not found in normalized devices" % device_path)


def _prime_normalized_paths():
    if _normalize_device_table == {}:
        lookup_paths = ["%s/*" % DISKBYIDPATH, "%s/*" % MAPPERPATH]

        for path in lookup_paths:
            for f in glob.glob(path):
                add_normalized_device(os.path.realpath(f), f)

        try:
            root = re.search('root=([^ $\n]+)', open('/proc/cmdline').read())
        except IOError:
            root = None

        if root and os.path.exists(root.group(1)):
            add_normalized_device('/dev/root', root.group(1))


def add_normalized_device(path, normalized_path):
    '''
    Add an entry to the normalized path list, adding to often does no harm and adding something that
    is not completely canonical does no harm either, because the search routine is recursive so if
    A=>B and B=>C then A,B and C will all evaluate to the canonical value of C.

    This routine does not add circular references, it is better to detect them in here than in the caller

    :param path: device path
    :param normalized_path: canonical path
    :return: No return value
    '''

    if (path != normalized_path):                           # Normalizing to itself makes no sense
        _normalize_device_table[path] = normalized_path


def add_normalized_list(raw_list, normalized_list):
    for key, path in raw_list.items():
        if key in normalized_list:
            add_normalized_device(path, normalized_list[key])
