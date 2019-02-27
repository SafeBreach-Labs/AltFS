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


FILE_NAME_1 = "FIRST_FILE"
FILE_NAME_2 = "SECOND_FILE"
DATA_1 = "HELLO_WORLD_HELLO_WORLD"
DATA_2 = "DATA!"


def perform_test_create_file(afs):
    file_1 = afs.create_file(FILE_NAME_1)
    assert isinstance(file_1, AltFS.File)
    assert file_1.get_pointer() == 0
    assert FILE_NAME_1 in afs.get_file_names()


def perform_test_read_file(afs):
    file_1 = afs.create_file(FILE_NAME_1)
    file_1.write(DATA_1)
    file_1.set_pointer(0)
    assert file_1.read(len(DATA_1)) == DATA_1


def perform_test_read_middle_of_file(afs):
    file_1 = afs.create_file(FILE_NAME_1)
    file_1.write(DATA_1)
    file_1.set_pointer(5)
    assert file_1.read(3) == DATA_1[5:8]
    assert file_1.get_pointer() == 8


def perform_test_write_file(afs):
    file_1 = afs.create_file(FILE_NAME_1)
    file_1.write(DATA_1)
    assert file_1.get_pointer() == len(DATA_1)
    file_1.set_pointer(0)
    assert file_1.read(len(DATA_1)) == DATA_1


def perform_test_seek_backwards(afs):
    file_1 = afs.create_file(FILE_NAME_1)
    file_1.write(DATA_1)
    file_1.seek(-5)
    assert file_1.get_pointer() == len(DATA_1) - 5
    assert file_1.read(6) == DATA_1[-5:]


def perform_test_write_in_middle_long_string(afs):
    file_1 = afs.create_file(FILE_NAME_1)
    file_1.write(DATA_1)
    file_1.set_pointer(1)
    long_size = afs.max_block_size * 3 + len(DATA_1) + 1
    file_1.write('x' * long_size)
    file_1.set_pointer(0)
    data = file_1.read(long_size * 4 + 1)
    assert data == DATA_1[0] + 'x' * long_size


def perform_test_write_in_middle_short_string(afs):
    file_1 = afs.create_file(FILE_NAME_1)
    file_1.write(DATA_1)
    replace_offset = len(DATA_1) / 2
    file_1.set_pointer(replace_offset)
    file_1.write('x')
    index = 0
    file_1.set_pointer(index)
    for index in xrange(len(DATA_1)):
        char = file_1.read(1)
        if index == replace_offset:
            assert char == 'x'
            continue
        assert char == DATA_1[index]
        index += 1


def perform_test_create_two_files(afs):
    afs.create_file(FILE_NAME_1)
    afs.create_file(FILE_NAME_2)
    files = afs.get_file_names()
    assert len(files) == 2


def perform_test_create_two_files_delete_first(afs):
    file_1 = afs.create_file(FILE_NAME_1)
    afs.create_file(FILE_NAME_2)
    file_1.delete()
    files = afs.get_file_names()
    assert len(files) == 1


def perform_test_create_two_files_delete_second(afs):
    afs.create_file(FILE_NAME_1)
    file_2 = afs.create_file(FILE_NAME_2)
    file_2.delete()
    files = afs.get_file_names()
    assert len(files) == 1
