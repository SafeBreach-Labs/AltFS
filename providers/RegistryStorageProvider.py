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


Storage provider implementation for AltFS, built on top of Windows Registry
System.

Terminology:
-    Bucket <-> Sub key of the base key (1 level down)
-    Value <-> Sub value inside a bucket

Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


import logging

from random import randint

import _winreg

from common.registry import get_sub_keys, \
    get_sub_values, \
    HIVES, \
    split_key_path_to_hive_and_path
from exceptions_ import BucketValueMissingException, \
    RegistryPathNotApplicableException
from providers.common.calculations import calculate_next_available_index
from StorageProvider import StorageProvider

logger = logging.getLogger(__name__)


class RegistryStorageProvider(StorageProvider):
    """
    Concrete Storage provider implementation for AltFS.

    Built on top of Windows Registry system.
    """

    def __init__(self, machine_identification_string, **kwargs):
        """Constructor for RegistryStorageProvider"""
        super(RegistryStorageProvider, self).__init__()
        # setup the base reg key
        hive, base_key_path = split_key_path_to_hive_and_path(
            kwargs["base_key_full_path"])
        self._base_key = _winreg.OpenKey(
            HIVES[hive], base_key_path, _winreg.KEY_SET_VALUE)
        # calculate number of available buckets, used for modulus division
        # when calculating the bucket index
        self._buckets_names = get_sub_keys(self._base_key)
        self._buckets_count = len(self._buckets_names)
        if self._buckets_count == 0:
            raise RegistryPathNotApplicableException(
                "No registry buckets(sub keys/values) available for storage")

    def write_block(self, bucket_id, value_id, data=""):
        """Described in parent class"""
        try:
            value_name = self._get_value_name(
                bucket_id, value_id)
        except BucketValueMissingException:
            logger.debug(
                "value with id does not exist in specified bucket." +
                " generating a new value name for bucket id %s" % bucket_id)
            value_name = self._generate_value_name(bucket_id)
            logger.debug("generated a new value name in bucket id %s: %s" % (
                bucket_id, value_name))
        with self._get_bucket_key(bucket_id, _winreg.KEY_WRITE) as key:
            _winreg.SetValueEx(key, value_name, 0,
                               _winreg.REG_BINARY, data)
        return RegistryStorageProvider.value_name_to_value_id(value_name)

    def get_block(self, bucket_id, value_id):
        """Described in parent class"""
        value_name = self._get_value_name(
            bucket_id, value_id)
        with self._get_bucket_key(bucket_id, _winreg.KEY_QUERY_VALUE) as key:
            data, _type = _winreg.QueryValueEx(key, value_name)
        return data

    def delete_block(self, bucket_id, value_id):
        """Described in parent class"""
        with self._get_bucket_key(bucket_id, _winreg.KEY_SET_VALUE) as key:
            _winreg.DeleteValue(key, self._get_value_name(
                bucket_id, value_id))

    def get_value_ids_in_bucket(self, bucket_id):
        """Described in parent class"""
        return self._enumerate_applicable_values_dict(bucket_id).keys()

    def generate_new_value_id_in_bucket(self, bucket_id):
        """Described in parent class"""
        return RegistryStorageProvider.value_name_to_value_id(
            self._generate_value_name(bucket_id))

    @staticmethod
    def value_name_to_value_id(value_name):
        """Returns the value ID of the given value_name"""
        return int(value_name[-4:])

    def _get_value_name(self, bucket_id, value_id):
        """Returns the value name in the given bucket ID, value ID"""
        values_dict = self._enumerate_applicable_values_dict(bucket_id)
        if value_id in values_dict:
            return values_dict[value_id]
        raise BucketValueMissingException(
            "No applicable value found in bucket")

    def _enumerate_applicable_values_dict(self, bucket_id):
        """
        Returns a mapping of value ID to value name.

        Values are all the AltFS applicable values inside the given bucket
        """
        values_names = self._enumerate_applicable_values(bucket_id)
        return dict(zip([RegistryStorageProvider.value_name_to_value_id(
            name) for name in values_names], values_names))

    def _enumerate_applicable_values(self, bucket_id):
        """
        Returns a list of value names.

        Values are all the AltFS applicable values inside the given bucket
        """
        with self._get_bucket_key(bucket_id) as bucket_key:
            return [name for name in get_sub_values(
                    bucket_key) if name != '' and
                    self._is_value_name_applicable(name)]

    def _get_bucket_key(self, bucket_id, desired_access=_winreg.KEY_READ):
        """Returns the Registry key that corresponds to the given bucket ID"""
        return _winreg.OpenKey(self._base_key,
                               self._get_bucket_name(bucket_id),
                               0,
                               desired_access)

    def _get_bucket_name(self, bucket_id):
        """Returns the bucket name of the bucket with the given ID"""
        return self._buckets_names[bucket_id]

    def _generate_value_name_machine_part(self):
        """
        Returns a new value name suffix.

        Called here the "machine part" of the value name.
        This value is chosen randomly out of the buckets names.
        """
        return self._buckets_names[randint(0, len(self._buckets_names) - 1)]

    def _generate_value_name(self, bucket_id):
        """Returns a new applicable value name in the given bucket ID"""
        return self._generate_value_name_machine_part() + "." + \
            ("%04d" % calculate_next_available_index(
                self._enumerate_applicable_values_dict(bucket_id).keys()))

    def _is_value_name_applicable(self, value_name):
        """
        Returns True if the given value name is AltFS applicable.

        Otherwise, returns False
        """
        return value_name[:-5] in self._buckets_names and \
            value_name[-5] == "." and all(
                [char.isdigit() for char in value_name[-4:]])
