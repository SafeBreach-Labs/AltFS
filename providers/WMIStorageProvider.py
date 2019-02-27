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


Storage provider implementation for AltFS, built on top of Windows WMI system.
system.

References:
-   https://www.blackhat.com/docs/us-15/materials/us-15-Graeber-Abusing-Windows
    -Management-Instrumentation-WMI-To-Build-A-Persistent%20Asynchronous-And-
    Fileless-Backdoor-wp.pdf
-   https://gallery.technet.microsoft.com/WMI-PowerShell-cmdlets-ac049637
-   https://docs.microsoft.com/en-us/windows/desktop/wmisdk/
    creating-a-base-class
-   https://stackoverflow.com/questions/252417/
    how-can-i-use-a-dll-file-from-python
-   https://docs.microsoft.com/en-us/windows/desktop/api/wbemcli/
    nn-wbemcli-iwbemservices

Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


import ctypes
import logging
import os

from common import WMI_CLIENT_DLL_PATH
from exceptions_ import BucketValueMissingException
from providers.common.calculations import calculate_bits_sum, \
    calculate_next_available_index
from StorageProvider import StorageProvider
import wmi

logger = logging.getLogger(__name__)


class WMIStorageProvider(StorageProvider):
    """
    Concrete Storage provider implementation for AltFS.

    Built on top of Windows WMI system (WBEM).
    """

    PROPERTY_NAME_DELIMITER = "_"
    TARGET_CLASS_NAME_SUFFIX = "Wow64_"

    def __init__(self, machine_identification_string, **kwargs):
        """Constructor for UserDefaultsStorageProvider"""
        super(WMIStorageProvider, self).__init__()
        self._machine_id_string = machine_identification_string
        self._wmi_client = wmi.WMI()
        self._wmi_client_dll = ctypes.cdll.LoadLibrary(
            os.path.join(os.path.dirname(__file__), WMI_CLIENT_DLL_PATH))
        self._namespace = kwargs["namespace"]
        self._class_name = self._generate_bucket_name()
        # calculate number of available buckets, used for modulus division
        # when calculating the bucket index
        self._buckets_names = [self._class_name]
        self._buckets_count = len(self._buckets_names)
        self._create_bucket()
        logger.debug("namespace: %s" % self._namespace)
        logger.debug("root class name: %s" % self._class_name)

    def _generate_bucket_name(self):
        classes = list([klass for klass in self._wmi_client.subclasses_of()
                        if not klass.startswith(
                            WMIStorageProvider.TARGET_CLASS_NAME_SUFFIX)])
        classes_count = len(classes)
        logger.debug("found %s legitimate classes" % classes_count)
        machine_id_checksum = calculate_bits_sum(
            self._machine_id_string)
        target_class_id = machine_id_checksum % classes_count - len(
            [
                klass for klass in list(
                    self._wmi_client.subclasses_of())[
                    :machine_id_checksum % classes_count] if klass.startswith(
                    WMIStorageProvider.TARGET_CLASS_NAME_SUFFIX)])
        logger.debug("target class for name generation: %s" %
                     (classes[target_class_id]))
        return WMIStorageProvider.TARGET_CLASS_NAME_SUFFIX + \
            classes[target_class_id].split("_")[-1]

    def _create_bucket(self):
        is_bucket_exist = self._class_name in self._wmi_client.subclasses_of()
        if is_bucket_exist:
            return
        p_ns = ctypes.c_wchar_p(self._namespace)
        p_cn = ctypes.c_wchar_p(self._class_name)
        logger.debug("creating class: %s\\%s" %
                     (self._namespace, self._class_name))
        self._wmi_client_dll.CreateClass(p_ns, p_cn)

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
        target_value_id = WMIStorageProvider.value_name_to_value_id(value_name)
        p_ns = ctypes.c_wchar_p(self._namespace)
        p_cn = ctypes.c_wchar_p(self._class_name)
        p_vn = ctypes.c_wchar_p(value_name)
        p_data = ctypes.c_wchar_p(data)
        logger.debug(
            "creating a new property at (%s:%s): %s\\%s.%s" %
            (bucket_id,
             target_value_id,
             self._namespace,
             self._class_name,
             value_name))
        self._wmi_client_dll.CreateProperty(p_ns, p_cn, p_vn, p_data)
        return target_value_id

    def get_block(self, bucket_id, value_id):
        """Described in parent class"""
        logger.debug("getting block at (%s:%s)" % (bucket_id, value_id))
        data = self._wmi_client.get(self._class_name).wmi_property(
            self._get_value_name(bucket_id, value_id)).value
        return data

    def delete_block(self, bucket_id, value_id):
        """Described in parent class"""
        value_name = self._get_value_name(
            bucket_id, value_id)
        p_ns = ctypes.c_wchar_p(self._namespace)
        p_cn = ctypes.c_wchar_p(self._class_name)
        p_vn = ctypes.c_wchar_p(value_name)
        logger.debug(
            "deleting a property at (%s:%s): %s\\%s.%s" %
            (bucket_id,
             WMIStorageProvider.value_name_to_value_id(value_name),
             self._namespace,
             self._class_name,
             value_name))
        self._wmi_client_dll.DeleteProperty(p_ns, p_cn, p_vn)

    def get_value_ids_in_bucket(self, bucket_id):
        """Described in parent class"""
        return self._enumerate_applicable_values_dict().keys()

    def generate_new_value_id_in_bucket(self, bucket_id):
        """Described in parent class"""
        return WMIStorageProvider.value_name_to_value_id(
            self._generate_value_name())

    @staticmethod
    def value_name_to_value_id(value_name):
        """Returns the value ID of the given value_name"""
        return int(value_name.split(
            WMIStorageProvider.PROPERTY_NAME_DELIMITER)[-1])

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
        return dict(zip([WMIStorageProvider.value_name_to_value_id(name)
                         for name in values_names], values_names))

    def _enumerate_applicable_values(self):
        return self._wmi_client.get(self._class_name).properties.keys()

    def _get_bucket_name(self, bucket_id):
        return self._buckets_names[bucket_id]

    def _generate_value_name_machine_part(self):
        return self._class_name.split(
            "_")[1] + WMIStorageProvider.PROPERTY_NAME_DELIMITER

    def _generate_value_name(self):
        return self._generate_value_name_machine_part() + \
            ("%04d" % calculate_next_available_index(
                self._enumerate_applicable_values_dict().keys()))

    def _is_value_name_applicable(self, value_name):
        return value_name.startswith(
            self._generate_value_name_machine_part()) and all(
            [char.isdigit() for char in value_name[-4:]])
