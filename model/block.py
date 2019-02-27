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

import msgpack

from providers.common.transformations import bytes_to_hex, hex_to_bytes


class Block(object):
    """
    The data structure of the virtual atomic write unit.

    This corresponds to a hard disk sector in the sense that it is the minimal
    unit for all R/W operations.
    Unlike a hard disk sector, the Block's size may vary.
    """

    # static values to be used as enum values
    TYPE_DESCRIPTOR = 0
    TYPE_DATA = 1

    def __init__(self, block_id=None,
                 block_type=None,
                 data_length=None,
                 next_block_id=None,
                 data=None):
        """Constructor for a Block instance"""
        self.block_id = block_id
        self.block_type = block_type
        self.data_length = data_length
        self.next_block_id = next_block_id
        self.data = data

    @staticmethod
    def generate_block_from_packed_str(packed_str):
        """Returns a Block built from a given serialized hex string"""
        block = Block()
        block.deserialize(packed_str)
        return block

    def serialize(self):
        """Returns the serialized inner dict of the instance, as hex string"""
        return bytes_to_hex(msgpack.packb(self.__dict__))

    def deserialize(self, packed_str):
        """Loads the given serialized hex string into the instance"""
        self.__dict__ = msgpack.unpackb(hex_to_bytes(packed_str))

    def __str__(self):
        """Returns a string representation of the instance"""
        return str(self.__dict__)
