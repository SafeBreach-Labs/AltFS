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


Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


import sys
sys.path.insert(0, '..')
import _winreg

from providers.common.registry import get_sub_keys, \
    get_sub_values, \
    HIVES, \
    split_key_path_to_hive_and_path


def get_bucket_key(base_key, bucket_name, desired_access=_winreg.KEY_READ):
    """Returns the Registry key that corresponds to the given bucket ID"""
    return _winreg.OpenKey(base_key, bucket_name, 0, desired_access)


def is_value_name_applicable(buckets_names, value_name):
    """
    Returns True if the given value name is AltFS applicable.

    Otherwise, returns False
    """
    return value_name[:-5] in buckets_names and value_name[-5] == "." and \
        all([char.isdigit() for char in value_name[-4:]])


def cleanup(base_key_full_path):
    """Performs the clean up of AltFS applicable values from the Registry"""
    hive, base_key_path = split_key_path_to_hive_and_path(base_key_full_path)
    with _winreg.OpenKey(
            HIVES[hive], base_key_path, _winreg.KEY_SET_VALUE) as base_key:
            buckets_names = get_sub_keys(base_key)

    for bucket_name in buckets_names:
        print "iterating key: %s" % bucket_name
        values_to_delete = []
        with get_bucket_key(
                HIVES[hive], "%s\\%s" % (base_key_path, bucket_name)) as key:
            for value_name in get_sub_values(key):
                print "iterating value name: %s" % value_name
                if is_value_name_applicable(buckets_names, value_name):
                    values_to_delete.append(value_name)

        with get_bucket_key(
            HIVES[hive], "%s\\%s" % (base_key_path, bucket_name),
                desired_access=_winreg.KEY_SET_VALUE) as key:
            for value_name in values_to_delete:
                print "-- going to delete: %s" % value_name
                _winreg.DeleteValue(key, value_name)


if __name__ == '__main__':
    cleanup(r"HKEY_CURRENT_USER\AppEvents\EventLabels")
