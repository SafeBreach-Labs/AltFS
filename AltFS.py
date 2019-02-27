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


Alternate Fileless File System
References:
Author: Dor Azouri <dor.azouri@safebreach.com>
Date: 2019-01-01
"""


import logging
import types

from exceptions_ import BucketValueMissingException, \
    EndOfFileReachedException, \
    FileIsClosedException, \
    FileNotFoundException, \
    InternalStorageOperationException, \
    UnsupportedProviderException
from model.block import Block
from model.descriptor import Descriptor
import providers
from providers.common.calculations import \
    calculate_bits_sum, \
    calculate_next_available_index, \
    split_string_by_max_size
from providers.common.machine_identification import \
    get_machine_identification_string


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AltFS(object):
    """
    Alternate Fileless File System.

    Base class for all usages
    """

    class File(object):
        """Provides a file-descriptor-like interface for AltFS files"""

        def __init__(self, altfs, name):
            """File constructor"""
            self._altfs = altfs
            self._pointer = 0
            self.name = name
            self._closed = False

        def _decorator(func):
            def check_closed(*args):
                self = args[0]
                if self._closed:
                    raise FileIsClosedException
                return func(*args)
            return check_closed

        def _set_open(self):
            """Explicitly sets the file status to OPEN"""
            self._closed = False

        @_decorator
        def get_pointer(self):
            """Returns the current pointer offset in file"""
            return self._pointer

        @_decorator
        def set_pointer(self, position):
            """Sets the pointer offset in file"""
            if position >= self.size():
                self._pointer = self.size()
            elif position < 0:
                self._pointer = 0
            else:
                self._pointer = position

        @_decorator
        def write(self, data):
            """Writes the given data to file, starting from the pointer"""
            self._altfs.write_file(self.name, self._pointer, data)

        @_decorator
        def read(self, size):
            """
            Returns data from file.

            starting from the pointer, and until the given size (in bytes)
            """
            return self._altfs.read_file(self.name, self._pointer, size)

        @_decorator
        def seek(self, offset):
            """
            Move the file pointer by the given offset.

            Offset may be negative
            """
            self._pointer += offset

        @_decorator
        def delete(self):
            """
            Deletes the file.

            The instance is not deleted, but set to CLOSED
            """
            self._closed = True
            self._altfs.delete_file(self.name)

        @_decorator
        def close(self):
            """Closes the file"""
            self._closed = True

        @_decorator
        def size(self):
            """Returns the file size"""
            return self._altfs.get_size(self.name)

        def __str__(self):
            """Returns the string representation of the file instance"""
            return "<File: name: %s, status: %s, pointer: %s, size: %s>" % \
                (self.name, "CLOSED" if self._closed else "OPEN",
                 self._pointer, self._altfs.get_size(self.name))

    def __init__(self, storage_provider_name, machine_identification_method,
                 max_block_size, **kwargs):
        """
        Constructor for a new AltFS.

        A new AltFS instance is created, given the storage provider name,
        the machine identification method name,
        and the desired maximal block size for that AltFS.

        Note:
        * Provider must reside in /providers and implement StorageProvider
        * Machine identification method name should be implemented in
          /providers/common/machine_identification.py and exported through
          the global METHODS dictionary.
        """
        logger.debug("initializing AltFS with storage provider: %s, " +
                     "machine identification method: %s" %
                     storage_provider_name, machine_identification_method)
        # calculate checksum of machine identification string, used for
        # calculating the bucket index of the first file system block
        machine_identification_string = get_machine_identification_string(
            machine_identification_method)
        self._set_machine_id_checksum(machine_identification_string)
        # initialize desired provider
        self._storage_providers = AltFS._load_providers()
        if storage_provider_name not in self._storage_providers:
            raise UnsupportedProviderException(storage_provider_name)
        self._storage_provider = \
            self._storage_providers[storage_provider_name](
                machine_identification_string, **kwargs)
        # set the buckets count, used for the modulus hash function
        self._buckets_count = self._storage_provider.get_buckets_count()
        # set the first bucket ID, used for the fs descriptor (superblock)
        self._first_bucket_id = \
            self._machine_id_checksum % self._buckets_count
        # set the max data block size
        self.max_block_size = max_block_size
        # log calculated initialization info
        logger.info("INIT:number of buckets (=divider): %s" %
                    self._buckets_count)
        logger.info("INIT:machine identification string: %s" %
                    machine_identification_string)
        logger.info("INIT:machine identification checksum: %s" %
                    self._machine_id_checksum)
        logger.info("INIT:first bucket ID: %s" %
                    self._first_bucket_id)
        # iterate all buckets in storage to fill the blocks mapping
        self._load_blocks_dict()
        # load the descriptor superblock/create fresh if it does not exist
        self._load_descriptor()
        # mapping of open files (volatile runtime File instances)
        self.files = {}

    def _set_machine_id_checksum(self, machine_identification_string):
        """Sets the calculated checksum of the machine identification string"""
        self._machine_id_checksum = calculate_bits_sum(
            machine_identification_string)

    @staticmethod
    def _load_providers():
        """
        Loads the available providers.

        Iterates provider modules in package, to dynamically obtain a list of
        available storage providers' names, and picks only the ones that
        implement the StorageProvider base class.
        """
        storage_providers = {}
        for symbol_name in dir(providers):
            symbol = getattr(providers, symbol_name)
            if not isinstance(symbol, (type, types.ClassType)):
                continue
            # fill only providers, i.e classes that derive from StorageProvider
            if issubclass(symbol, providers.StorageProvider) and \
                    symbol != providers.StorageProvider:
                storage_providers[symbol_name] = symbol
        return storage_providers

    def _load_blocks_dict(self):
        """
        Fills the mapping of {block_id : (bucket_id, value_id)}.

        Iterates through all values in all buckets in storage. Determining
        which of the iterated values are part of the virtual FS is
        provider-dependent.

        Note: the filling policy is naive - any exception in the storage layer
        is ignored, and iteration continues to next bucket.
        """
        self._blocks_dict = {}
        for bucket_id in xrange(self._buckets_count):
            try:
                values = self._storage_provider.get_value_ids_in_bucket(
                    bucket_id)
            except Exception as e:
                logger.error(e, exc_info=True)
                continue
            for value_id in values:
                block = self._get_block(bucket_id, value_id)
                self._blocks_dict[block.block_id] = (bucket_id, value_id)

    def _load_descriptor(self):
        """
        Loads the descriptor instance from the superblock.

        Creates an empty descriptor if such block does not exist,
        and writes it to storage.
        """
        self._descriptor = Descriptor()
        try:  # try load the existing descriptor from superblock
            first_block_data = self._storage_provider.get_block(
                self._first_bucket_id, 0)
            block = Block.generate_block_from_packed_str(first_block_data)
            self._descriptor.__dict__ = block.data
        except BucketValueMissingException:  # superblock does not exist
            logger.error("superblock does not exist. Creating a new empty one")
            # create an empty descriptor and write it as a superblock (id=0)
            self._write_block(
                self._first_bucket_id, 0, self._generate_descriptor_block())

    def _get_next_available_block_id(self, count=1, blacklist=None):
        """
        Returns the next _count_ available block IDs.

        Considering the IDs given in the blacklist parameter.
        The next ID is the lowest available (re-use)
        """
        if blacklist is None:
            blacklist = []
        ids = []
        existing_ids = self._blocks_dict.keys() + blacklist
        for i in xrange(count):
            id_ = calculate_next_available_index(existing_ids)
            ids.append(id_)
            existing_ids.append(id_)
        if count == 1:
            return ids[0]
        return ids

    def _get_block(self, bucket_id, value_id):
        """
        Loads the block the data from the desired value.

        Returns it as aBlock instance.
        Raises InternalStorageOperationException if provider has failed to read
        """
        try:
            block = Block.generate_block_from_packed_str(
                self._storage_provider.get_block(bucket_id, value_id))
        except Exception as e:
            logger.error("reading of block at (%s:%s) has failed: %s" %
                         (bucket_id, value_id, str(e)))
            raise InternalStorageOperationException(
                InternalStorageOperationException.OPERATION_READ, str(e))
        logger.debug("a block was read at (%s:%s):%s" %
                     (bucket_id, value_id, block.__dict__))
        return block

    def _get_block_by_id(self, block_id):
        """Returns a Block instance of the desired block ID."""
        return self._get_block(*self._blocks_dict[block_id])

    def _generate_data_termination_block(self, data="", block_id=None):
        """
        Returns a Block instance to be used as the last data block of a file.

        It closes the chain of data blocks by pointing to the superblock as
        next block.
        """
        new_block_id = block_id if block_id is not None else \
            self._get_next_available_block_id()
        return Block(block_id=new_block_id,
                     block_type=Block.TYPE_DATA,
                     data_length=len(data),
                     next_block_id=0,
                     data=data)

    def _generate_descriptor_block(self):
        """
        Returns a Block instance of type TYPE_DESCRIPTOR.

        The current descriptor object is saved to it.

        Note: The next block ID field is redundant so it's given a constant 1.
        """
        return Block(block_id=0,
                     block_type=Block.TYPE_DESCRIPTOR,
                     data_length=len(self._descriptor.serialize()),
                     next_block_id=1,
                     data=self._descriptor.__dict__)

    def _write_block(self, bucket_id, value_id, block):
        """
        Writes the given Block instance to the given value_id.

        Overrides the existing one.
        Returns the value ID to which the block was written.

        Note: if the given value ID is None, a new value is created in the
        given bucket, and the block is written to it

        Raises InternalStorageOperationException if provider failed to write
        """
        logger.debug("writing block at (%s:%s):%s" %
                     (bucket_id, value_id, block.__dict__))
        try:
            value_id = self._storage_provider.write_block(
                bucket_id, value_id, data=block.serialize())
        except Exception as e:
            logger.error("writing of block (id:%s) to (%s:%s) has failed: %s" %
                         (block.block_id, bucket_id, value_id, str(e)))
            raise InternalStorageOperationException(
                InternalStorageOperationException.OPERATION_WRITE, str(e))
        # add the new block mapping
        self._blocks_dict[block.block_id] = (bucket_id, value_id)
        return value_id

    def _get_blocks_generator(self, start_block_id):
        """
        A generator for blocks in a linked chain.

        Starting from the given block ID, ending in the data termination block.
        """
        bucket_id, value_id = self._blocks_dict[start_block_id]
        while True:
            block = self._get_block(bucket_id, value_id)
            if block.block_id == 0:
                break
            yield block
            bucket_id, value_id = self._blocks_dict[block.next_block_id]

    def _delete_value(self, bucket_id, value_id):
        """
        Deletes the value in the given bucket and value IDs.

        Raises InternalStorageOperationException if provider failed to delete
        """
        block = self._get_block(bucket_id, value_id)
        logger.debug("deleting block ID %s (%s:%s)" %
                     (block.block_id, bucket_id, value_id))
        try:
            self._storage_provider.delete_block(bucket_id, value_id)
        except Exception as e:
            logger.error(
                "deleting of block (id:%s) to (%s:%s) has failed: %s" %
                (block.block_id, bucket_id, value_id, str(e)))
            raise InternalStorageOperationException(
                InternalStorageOperationException.OPERATION_DELETE, str(e))
        # remove the mapping of the deleted block
        del self._blocks_dict[block.block_id]

    def _delete_data_blocks(self, start_block_id, until_block_id=None):
        """
        Delete a chain of linked blocks.

        Starting from the given block ID, ending in the data termination block.
        """
        for block in list(self._get_blocks_generator(start_block_id)):
            if until_block_id is not None and block.block_id == until_block_id:
                break
            bucket_id, value_id = self._blocks_dict[block.block_id]
            self._delete_value(bucket_id, value_id)

    def _get_block_by_file_offset(self, file_name, offset):
        """
        Returns a tuple of: (block, offset inside block).

        The block is the one in which the given offset is located
        """
        start_block_id = self._descriptor.files_dict[file_name]
        position = 0
        for block in self._get_blocks_generator(start_block_id):
            if position <= offset <= position + block.data_length:
                return block, offset - position
            position += block.data_length
        raise EndOfFileReachedException(
            "The given offset exceeds the file size")

    def _create_data_blocks(self, data, terminating_at=None):
        """
        Writes a chain of data blocks to hold the given data.

        Optional terminating_at parameter defines the next_block_id of the last
        data block in the chain. If omitted, the chain ends at the superblock.
        """
        if len(data) == 0:
            return []
        chunks = list(split_string_by_max_size(data, self.max_block_size))
        new_block_ids = self._get_next_available_block_id(count=len(chunks))
        if isinstance(new_block_ids, int):
            new_block_ids = [new_block_ids]
        if terminating_at:
            new_block_ids.append(terminating_at)
        else:
            new_block_ids.append(self._get_next_available_block_id(
                count=1, blacklist=new_block_ids))

        chunk = ""
        for chunk_id, chunk in zip(range(len(chunks)), chunks):
            new_block = Block(block_id=new_block_ids[chunk_id],
                              block_type=Block.TYPE_DATA,
                              data_length=len(chunk),
                              next_block_id=new_block_ids[chunk_id + 1],
                              data=chunk)
            bucket_id = calculate_bits_sum(chunk) % self._buckets_count
            self._write_block(bucket_id, None, new_block)

        if not terminating_at:
            new_block = self._generate_data_termination_block(
                block_id=new_block_ids[-1])
            bucket_id = calculate_bits_sum(chunk) % self._buckets_count
            self._write_block(bucket_id, None, new_block)
        return new_block_ids

    def _update_block(self, block_id, **kwargs):
        logging.debug("updating block (id=%s) with kwargs:%s" %
                      (block_id, str(kwargs)))
        block = self._get_block_by_id(block_id)
        bucket_id, value_id = self._blocks_dict[block.block_id]
        for k, v in kwargs.iteritems():
            setattr(block, k, v)
        self._write_block(bucket_id, value_id, block)

    def create_file(self, file_name):
        """
        Returns a File object of the given name.

        Note:
        *   If a file with that name already exists, it's corresponding File
            instance is returned.
        *   Otherwise, the required data blocks are written to storage, and a
            corresponding File instance is returned.
        """
        if file_name in self.files:
            # in case a File object already exists - return it
            self.files[file_name]._set_open()
            self.files[file_name].set_pointer(0)
            return self.files[file_name]
        if file_name not in self._descriptor.files_dict:
            # in case file doesn't exist in storage - create it.
            # creating a new empty file means adding only a single data
            # termination block, as there are no actual data blocks yet
            block = self._generate_data_termination_block()
            # adding the required mapping needed in the descriptor:
            self._descriptor.add_file(file_name, block.block_id)
            # flushing the new descriptor after update, into storage
            self._write_block(
                self._first_bucket_id, 0, self._generate_descriptor_block())
            # calculate the target bucket ID for the new block, by applying the
            # hash function on the file name
            target_bucket_id = calculate_bits_sum(
                file_name) % self._buckets_count
            # write the data termination block to the calculated bucket,
            # creating a new value by passing None as the value ID
            value_id = self._write_block(
                target_bucket_id, None, block)
            # add the new block mapping
            self._blocks_dict[block.block_id] = (
                target_bucket_id, value_id)
        # in case the file exists in storage, a new File instance is created.
        # We also do it in case we have just created the actual file in storage
        self.files[file_name] = AltFS.File(self, file_name)
        return self.files[file_name]

    def delete_file(self, file_name):
        """
        Deletes a file.

        Results in:
        *   Deletion of all of the file's data blocks, including the data
            termination block.
        *   Removal of the mappings of the file's blocks
        *   Deletion of the corresponding File instance.
        *   Removal of the file mapping from the descriptor
            (updates the descriptor superblock in storage)
        """
        if file_name not in self._descriptor.files_dict:
            raise FileNotFoundException("Cannot delete a non-existent file")
        block_id = self._descriptor.files_dict[file_name]
        self._delete_data_blocks(block_id)
        del self.files[file_name]
        # remove the file from the descriptor object
        self._descriptor.remove_file(file_name)
        # write the update descriptor to storage
        self._write_block(
            self._first_bucket_id, 0, self._generate_descriptor_block())

    def read_file(self, file_name, start, size):
        """
        Returns the data from file given its name.

        Starting from given offset and up to a maximum given size.
        """
        if file_name not in self._descriptor.files_dict:
            raise FileNotFoundException()
        data = ""
        position = 0
        first_file_block = self._descriptor.files_dict[file_name]
        for block in self._get_blocks_generator(first_file_block):
            data += block.data
            position += block.data_length
            if position >= start + size:
                break

        self.files[file_name].set_pointer(start + size)
        return data[start:start + size]

    def write_file(self, file_name, start, data):
        """
        Writes the given data to file given its name.

        Starting from given offset.
        """
        # in case data to write exceeds the current file size, create new
        # blocks that will be later linked with the block where start is
        # located. The overall result in this case should look like this:
        # [current blocks...] -> [fork block] -> [new blocks] -> [superblock]
        if start + len(data) >= self.get_size(file_name):
            # create the data blocks, still not linked, hanging in the air
            new_block_ids = self._create_data_blocks(data)
            # the new blocks anyway exceed the current file size, so no need to
            # connect the end of the new chain back to a current block
            until_block_id = None
            # calculate the the starting block out of the current file blocks,
            # that will link to the new blocks
            fork_block, offset_in_fork_block = self._get_block_by_file_offset(
                file_name, start)
        # in case data to write fits into the file size, we need to link the
        # new data blocks from both sides. Eventually, it should look like
        # this:
        # [current blocks...] -> [fork block] -> [new blocks] ->
        # [merging block] -> [current blocks...] -> [superblock]
        else:
            # calculate the block to which the new blocks end should link to
            merging_block, offset_in_merging_block = \
                self._get_block_by_file_offset(
                    file_name, start + len(data) - 1)
            # calculate the the starting block out of the current file blocks,
            # that will link to the new blocks
            fork_block, offset_in_fork_block = self._get_block_by_file_offset(
                file_name, start)
            # handle edge case where the fork and merging blocks are the same.
            # in this case, we just need to override that block's data
            if fork_block.block_id == merging_block.block_id:
                new_data = fork_block.data[:offset_in_fork_block] + \
                    data + fork_block.data[offset_in_fork_block + len(data):]
                self._update_block(fork_block.block_id,
                                   data=new_data, data_length=len(new_data))
                self.files[file_name].set_pointer(start + len(data))
                return
            # in the general case, we create new data blocks to be connected as
            # described, and cut data from the merging block, as the new data
            # length demands
            else:
                new_block_ids = self._create_data_blocks(
                    data, terminating_at=merging_block.block_id)
                if offset_in_merging_block < merging_block.data_length:
                    new_data = merging_block.data[offset_in_merging_block:]
                    self._update_block(
                        merging_block.block_id,
                        data=new_data,
                        data_length=len(new_data))
                until_block_id = merging_block.block_id

        # cut the data in the fork block, as the start offset demands
        if offset_in_fork_block < fork_block.data_length:
            new_data = fork_block.data[:offset_in_fork_block]
            self._update_block(fork_block.block_id,
                               data=new_data, data_length=len(new_data))

        # delete the current blocks, starting from the fork block and ending at
        # the merging block/super block (depends on the above case - each case
        # sets the until_block_id value accordingly)
        self._delete_data_blocks(
            fork_block.next_block_id, until_block_id=until_block_id)
        self._update_block(fork_block.block_id, next_block_id=new_block_ids[0])

        self.files[file_name].set_pointer(start + len(data))
        return

    def get_file_names(self):
        """Returns the names of all files currently in storage"""
        return self._descriptor.get_file_names()

    def get_size(self, file_name):
        """Returns the size of file, given its name"""
        file_size = 0
        first_file_block = self._descriptor.files_dict[file_name]
        for block in self._get_blocks_generator(first_file_block):
            file_size += block.data_length
        return file_size
