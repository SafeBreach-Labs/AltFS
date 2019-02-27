#!/usr/bin/env python
"""
BSD 3-Clause License

Copyright (c) 2017, SafeBreach Labs
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Helper functions for Windows registry operations
Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


import logging

import _winreg


logger = logging.getLogger(__name__)


HIVES = {
    "HKEY_CLASSES_ROOT": _winreg.HKEY_CLASSES_ROOT,
    "HKEY_CURRENT_CONFIG": _winreg.HKEY_CURRENT_CONFIG,
    "HKEY_CURRENT_USER": _winreg.HKEY_CURRENT_USER,
    "HKEY_LOCAL_MACHINE": _winreg.HKEY_LOCAL_MACHINE,
    "HKEY_USERS": _winreg.HKEY_USERS,
}
WIN_ERROR_NO_MORE_DATA = 259


def get_sub_keys(key):
    """Returns a list of all sub keys under the given registry key"""
    index = 0
    sub_keys = []
    while True:
        try:
            sub_keys.append(_winreg.EnumKey(key, index))
            index += 1
        except WindowsError as e:
            if not (hasattr(e, "winerror") and e.winerror ==
                    WIN_ERROR_NO_MORE_DATA):
                logger.error(e, exc_info=True)
            break
    return sub_keys


def get_sub_values(key):
    """Returns a list of all sub values under the given registry key"""
    index = 0
    sub_values = []
    while True:
        try:
            sub_values.append(_winreg.EnumValue(key, index)[0])
            index += 1
        except WindowsError as e:
            if not (hasattr(e, "winerror") and e.winerror ==
                    WIN_ERROR_NO_MORE_DATA):
                logger.error(e, exc_info=True)
            break
    return sub_values


def split_key_path_to_hive_and_path(key_path):
    """Return a (hive, path) tuple given a full key path"""
    path_parts = key_path.split("\\")
    hive = path_parts[0]
    path = "\\".join(path_parts[1:])
    return hive, path
