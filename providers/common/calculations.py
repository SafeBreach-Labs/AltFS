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


Helper functions performing various calculations
Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


from math import ceil


def calculate_bits_sum(string):
    """Returns the bits sum of the string characters' ASCII values"""
    return sum([bin(ord(char)).count("1") for char in string])


def calculate_next_available_index(indexes):
    """
    Returns the next available index.

    Given a list of indexes.
    Uses UNIX's next file descriptor algorithm.
    """
    if not indexes:
        return 0
    length = len(indexes)
    for i in xrange(length):
        if i not in indexes:
            return i
    return max(indexes) + 1


def calculate_required_chunks_by_max_size(data, max_size):
    """
    Returns the number of chunks required for storing the given data.

    Given the maximal chunk size
    """
    return int(ceil(len(data) / float(max_size)))


def split_string_by_max_size(string, max_size):
    """
    A generator returning chunks out of the given string.

    Each not exceeding the given size
    """
    while string:
        yield string[:max_size]
        string = string[max_size:]
