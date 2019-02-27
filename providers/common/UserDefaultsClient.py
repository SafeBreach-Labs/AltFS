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


User Defaults client class, wrapping calls to CoreFoundation framework API.

References:
-   https://stackoverflow.com/questions/51749443/getting-plist-file-location-
    created-by-cfpreferences-with-kcfpreferencesanyuser
-   http://macadmins.psu.edu/wp-content/uploads/sites/24696/2015/07/psumac2015
    -62-Working_with_System_Frameworks_in_Python_and_Objective-C.pdf

Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


from Foundation import CFPreferencesCopyKeyList, \
    CFPreferencesCopyValue, \
    CFPreferencesSetValue, \
    kCFPreferencesAnyApplication, \
    kCFPreferencesAnyHost, \
    kCFPreferencesCurrentUser


class UserDefaultsClient(object):
    """A helper class for macOS Foundation Core API functions"""

    @staticmethod
    def get_keys():
        """Returns a list of the names of the keys in Defaults"""
        return CFPreferencesCopyKeyList(
            kCFPreferencesAnyApplication,
            kCFPreferencesCurrentUser,
            kCFPreferencesAnyHost)

    @staticmethod
    def get_key(key):
        """Returns the keys in Defaults"""
        return CFPreferencesCopyValue(
            key,
            kCFPreferencesAnyApplication,
            kCFPreferencesCurrentUser,
            kCFPreferencesAnyHost)

    @staticmethod
    def write_key(key, value):
        """Writes the given value to the given key"""
        CFPreferencesSetValue(
            key,
            value,
            kCFPreferencesAnyApplication,
            kCFPreferencesCurrentUser,
            kCFPreferencesAnyHost)

    @staticmethod
    def delete_key(key):
        """Deletes the given key"""
        CFPreferencesSetValue(
            key,
            None,
            kCFPreferencesAnyApplication,
            kCFPreferencesCurrentUser,
            kCFPreferencesAnyHost)
