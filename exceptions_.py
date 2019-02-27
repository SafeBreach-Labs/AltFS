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


Custom exceptions
Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


class UnsupportedProviderException(Exception):
    """Custom exception"""

    pass


class ArgumentException(Exception):
    """Custom exception"""

    pass


class RegistryPathNotApplicableException(Exception):
    """Custom exception"""

    pass


class BucketValueMissingException(Exception):
    """Custom exception"""

    pass


class FileNameAlreadyExistsException(Exception):
    """Custom exception"""

    pass


class FileNotFoundException(Exception):
    """Custom exception"""

    pass


class FileIsClosedException(Exception):
    """Custom exception"""

    pass


class EndOfFileReachedException(Exception):
    """Custom exception"""

    pass


class InternalStorageOperationException(Exception):
    """
    Custom exception.

    Used to indicate provider-specific failure in one of the basic operations.
    """

    OPERATION_READ = "READ"
    OPERATION_WRITE = "WRITE"
    OPERATION_DELETE = "DELETE"

    def __init__(self, operation, msg):
        """
        Constructor for the custom Exception.

        Sets the message attribute of the base Exception class
        """
        self.message = "Provider operation (%s) has failed internally: %s" % (
        operation, msg)
