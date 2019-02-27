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


Storage provider "abstract" class. Any new storage provider must implement all
of the defined methods.

Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


class StorageProvider(object):
    """Base class for AltFS Storage Providers"""

    def __init__(self, **kwargs):
        """
        Initializes the storage source to allow further operations.

        Buckets count is suggested to be performed here and be fixated to the
        instance, to allow consistency in indexing calculations
        """
        self._buckets_count = 0

    def get_buckets_count(self):
        """Returns the number of available buckets in the storage"""
        return self._buckets_count

    def write_block(self, bucket_id, value_id, data=""):
        """
        Writes the given data to the given bucket ID, value ID.

        The data is written raw into the storage value, so it must be an
        already serialized Block.
        In case bucket ID does not exist - this is a fatal error that is caused
        by major storage change/corruption, and is not handled.
        In case value ID does not exist in bucket, a new value is created with
        a name generated using the generate_new_value_id_in_bucket function.
        """
        raise NotImplementedError()

    def get_block(self, bucket_id, value_id):
        """
        Returns the raw data of the block in the given bucket ID, value ID.

        In case bucket ID does not exist - this is a fatal error that is caused
        by major storage change/corruption, and is not handled.
        In case value ID does not exist in bucket, raises
        BucketValueMissingException.
        """
        raise NotImplementedError()

    def delete_block(self, bucket_id, value_id):
        """
        Deletes a value from storage in the given bucket ID, value ID.

        In case bucket ID does not exist - this is a fatal error that is caused
        by major storage change/corruption, and is not handled.
        In case value ID does not exist in bucket, raises
        BucketValueMissingException.
        """
        raise NotImplementedError()

    def get_value_ids_in_bucket(self, bucket_id):
        """
        Returns a list of value IDs of the existing values in the given bucket.

        In case bucket ID does not exist - this is a fatal error that is caused
        by major storage change/corruption, and is not handled.
        """
        raise NotImplementedError()

    def generate_new_value_id_in_bucket(self, bucket_id):
        """Returns a new available value ID in the given bucket"""
        raise NotImplementedError()

    def _is_value_name_applicable(self, value_name):
        """
        Returns True if given value name is AltFS applicable.

        Otherwise, returns False.
        """
        raise NotImplementedError()
