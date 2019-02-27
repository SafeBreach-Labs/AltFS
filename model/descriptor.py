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


Block data structure for AltFS.
Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


import sys
sys.path.insert(0, '..')

from exceptions_ import FileNameAlreadyExistsException, FileNotFoundException
import msgpack
from providers.common.transformations import bytes_to_hex, hex_to_bytes


class Descriptor(object):
    """
    The data structure of the FS descriptor.

    This object lives in the first block of the AltFS blocks chain
    (aka superblock, root block)
    """

    def __init__(self, files_dict=None):
        """Constructor for a Descriptor instance"""
        # a mapping of: file name <-> ID of the first block of that file data
        if files_dict is None:
            files_dict = {}
        self.files_dict = files_dict

    def add_file(self, file_name, start_block_id):
        """
        Adds a new file mapping.

        Given the file name and the ID of the first block of that file data
        """
        if file_name in self.files_dict:
            raise FileNameAlreadyExistsException()
        self.files_dict[file_name] = start_block_id

    def remove_file(self, file_name):
        """Removes the file mapping of the given file name"""
        if file_name not in self.files_dict:
            raise FileNotFoundException()
        del self.files_dict[file_name]

    def get_file_names(self):
        """Returns all of the existing file names currently in the AltFS"""
        return self.files_dict.keys()

    def serialize(self):
        """Returns the serialized inner dict of the instance, as hex string"""
        return bytes_to_hex(msgpack.packb(self.__dict__))

    def deserialize(self, packed_str):
        """Loads the given serialized hex string into the instance"""
        self.__dict__ = msgpack.unpackb(hex_to_bytes(packed_str))

    def __str__(self):
        """Returns a string representation of the instance"""
        return str(self.__dict__)
