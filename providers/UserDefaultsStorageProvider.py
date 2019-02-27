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


Storage provider implementation for AltFS, built on top of MacOS User Defaults
system.

Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


import logging

from common.UserDefaultsClient import UserDefaultsClient
from exceptions_ import BucketValueMissingException
from providers.common.calculations import calculate_next_available_index
from StorageProvider import StorageProvider

logger = logging.getLogger(__name__)


class UserDefaultsStorageProvider(StorageProvider):
    """
    Concrete Storage provider implementation for AltFS.

    Built on top of macOS User Defaults system.
    """

    TARGET_KEY_NAME_SUFFIX = "NSApplex64"
    KEY_NAME_DELIMITER = "_"

    def __init__(self, machine_identification_string, **kwargs):
        """Constructor for UserDefaultsStorageProvider"""
        super(UserDefaultsStorageProvider, self).__init__()
        self._machine_id_string = machine_identification_string
        self._defaults_client = UserDefaultsClient
        # self._domain_name = self._generate_bucket_name()
        self._domain_name = "NSGlobalDomain"
        # calculate number of available buckets, used for modulus division
        # when calculating the bucket index
        self._buckets_names = [self._domain_name]
        self._buckets_count = len(self._buckets_names)
        logger.debug("domain: %s" % self._domain_name)

    def write_block(self, bucket_id, value_id, data=""):
        """Described in parent class"""
        logger.debug("writing block at (%s:%s)" % (bucket_id, value_id))
        try:
            value_name = self._get_value_name(
                bucket_id, value_id)
            logger.debug("value with id already exists at (%s:%s)" %
                         (bucket_id, value_id))
        except BucketValueMissingException:
            logger.debug(
                "value with id does not exist in specified bucket." +
                " generating a new value name for bucket id %s" % bucket_id)
            value_name = self._generate_value_name()
            logger.debug("generated a new value name in bucket id %s: %s" % (
                bucket_id, value_name))
        target_value_id = UserDefaultsStorageProvider.value_name_to_value_id(
            value_name)
        logger.debug("creating a new key at (%s:%s): %s" % (
            bucket_id, target_value_id, value_name))
        self._defaults_client.write_key(value_name, data)
        return target_value_id

    def get_block(self, bucket_id, value_id):
        """Described in parent class"""
        logger.debug("getting block at (%s:%s)" % (bucket_id, value_id))
        data = self._defaults_client.get_key(
            self._get_value_name(bucket_id, value_id))
        return data

    def delete_block(self, bucket_id, value_id):
        """Described in parent class"""
        value_name = self._get_value_name(
            bucket_id, value_id)
        logger.debug(
            "deleting a key at (%s:%s): %s" %
            (bucket_id,
             UserDefaultsStorageProvider.value_name_to_value_id(value_name),
             value_name))
        self._defaults_client.delete_key(value_name)

    def get_value_ids_in_bucket(self, bucket_id):
        """Described in parent class"""
        return self._enumerate_applicable_values_dict().keys()

    def generate_new_value_id_in_bucket(self, bucket_id):
        """Described in parent class"""
        return UserDefaultsStorageProvider.value_name_to_value_id(
            self._generate_value_name())

    @staticmethod
    def value_name_to_value_id(value_name):
        """Returns the value ID of the given value_name"""
        return int(value_name.split(
            UserDefaultsStorageProvider.KEY_NAME_DELIMITER)[-1])

    def _get_value_name(self, bucket_id, value_id):
        logger.debug("looking for value name at (%s:%s)" %
                     (bucket_id, value_id))
        if value_id is not None:
            values_dict = self._enumerate_applicable_values_dict()
            logger.debug("existing values: %s" % values_dict)
            if value_id in values_dict:
                logger.debug("value name exists at (%s:%s): %s" %
                             (bucket_id, value_id, values_dict[value_id]))
                return values_dict[value_id]
        logger.debug("no value name at (%s:%s)" % (bucket_id, value_id))
        raise BucketValueMissingException(
            "No applicable value found in bucket")

    def _enumerate_applicable_values_dict(self):
        values_names = self._enumerate_applicable_values()
        return dict(zip([UserDefaultsStorageProvider.value_name_to_value_id(
            name) for name in values_names], values_names))

    def _enumerate_applicable_values(self):
        return [k for k in self._defaults_client.get_keys(
        ) if self._is_value_name_applicable(k)]

    def _get_bucket_name(self, bucket_id):
        return self._buckets_names[bucket_id]

    @staticmethod
    def _generate_value_name_machine_part():
        return UserDefaultsStorageProvider.TARGET_KEY_NAME_SUFFIX + \
            UserDefaultsStorageProvider.KEY_NAME_DELIMITER

    def _generate_value_name(self):
        return \
            UserDefaultsStorageProvider._generate_value_name_machine_part() + \
            ("%04d" % calculate_next_available_index(
                self._enumerate_applicable_values_dict().keys()))

    def _is_value_name_applicable(self, value_name):
        return value_name.startswith(
            UserDefaultsStorageProvider.TARGET_KEY_NAME_SUFFIX)
