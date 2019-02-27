from persistency import simple_set_up, get_file_names
from file_operations import *
from AltFS import AltFS
import pytest


global afs
afs = AltFS("WMIStorageProvider", "network_card",
            namespace="root\\cimv2", max_block_size=100)


def test_create_file_WMIStorageProvider():
    global afs
    perform_test_create_file(afs)


def test_read_file_WMIStorageProvider():
    global afs
    perform_test_read_file(afs)


def test_read_middle_of_file_WMIStorageProvider():
    global afs
    perform_test_read_middle_of_file(afs)


def test_write_file_WMIStorageProvider():
    global afs
    perform_test_write_file(afs)


def test_seek_backwards_WMIStorageProvider():
    global afs
    perform_test_seek_backwards(afs)


def test_write_in_middle_short_string_WMIStorageProvider():
    global afs
    perform_test_write_in_middle_short_string(afs)


def test_create_two_files_WMIStorageProvider():
    global afs
    perform_test_create_two_files(afs)


def test_create_two_files_delete_first_WMIStorageProvider():
    global afs
    perform_test_create_two_files_delete_first(afs)


def test_create_two_files_delete_second_WMIStorageProvider():
    global afs
    perform_test_create_two_files_delete_second(afs)


def test_persistency_WMIStorageProvider():
    afs1 = AltFS("WMIStorageProvider", "network_card",
                 namespace="root\\cimv2", max_block_size=100)
    simple_set_up(afs1)
    first_time_files = get_file_names(afs1)

    afs2 = AltFS("WMIStorageProvider", "network_card",
                 namespace="root\\cimv2", max_block_size=100)
    second_time_files = get_file_names(afs2)

    assert first_time_files == second_time_files
