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

from AltFS import AltFS
from file_operations import *
from persistency import simple_set_up, get_file_names


global afs
afs = AltFS(
    "RegistryStorageProvider",
    "network_card",
    base_key_full_path=r"HKEY_CURRENT_USER\AppEvents\EventLabels",
    max_block_size=10)


def test_create_file_RegistryStorageProvider():
    global afs
    perform_test_create_file(afs)


def test_read_file_RegistryStorageProvider():
    global afs
    perform_test_read_file(afs)


def test_read_middle_of_file_RegistryStorageProvider():
    global afs
    perform_test_read_middle_of_file(afs)


def test_write_file_RegistryStorageProvider():
    global afs
    perform_test_write_file(afs)


def test_seek_backwards_RegistryStorageProvider():
    global afs
    perform_test_seek_backwards(afs)


def test_write_in_middle_short_string_RegistryStorageProvider():
    global afs
    perform_test_write_in_middle_short_string(afs)


def test_create_two_files_RegistryStorageProvider():
    global afs
    perform_test_create_two_files(afs)


def test_create_two_files_delete_first_RegistryStorageProvider():
    global afs
    perform_test_create_two_files_delete_first(afs)


def test_create_two_files_delete_second_RegistryStorageProvider():
    global afs
    perform_test_create_two_files_delete_second(afs)


def test_persistency_RegistryStorageProvider():
    afs1 = AltFS(
        "RegistryStorageProvider",
        "network_card",
        base_key_full_path=r"HKEY_CURRENT_USER\AppEvents\EventLabels",
        max_block_size=10)
    simple_set_up(afs1)
    first_time_files = get_file_names(afs1)

    afs2 = AltFS(
        "RegistryStorageProvider",
        "network_card",
        base_key_full_path=r"HKEY_CURRENT_USER\AppEvents\EventLabels",
        max_block_size=10)
    second_time_files = get_file_names(afs2)

    assert first_time_files == second_time_files
