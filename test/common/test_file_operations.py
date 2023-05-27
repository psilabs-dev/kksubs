# TODO: test expected file operation behavior (utils/file)

# test unidirectional file sync with removing deleted files
# test unidirectional file sync without removing deleted files
# test bidirectional file sync

import os
import tempfile
import unittest

from common.utils.file import *

def create_files_in_directory(parent_directory, files):
    if files is None or not files:
        return
    for file in files:
        dirname = os.path.join(parent_directory, os.path.dirname(file))
        file_path = os.path.join(parent_directory, file)
        os.makedirs(dirname, exist_ok=True)
        with open(file_path, 'w') as writer:
            writer.write('')

def get_files_in_directory(directory):
    reg_files = set()
    for root, _, files in os.walk(directory):
        for file in files:
            reg_files.add(os.path.relpath(os.path.join(root, file), directory))
    return reg_files

class TestFileOperations(unittest.TestCase):

    def setUp(self) -> None:
        self.source_files = {
            'abc'
        }
        self.dest_files = {
            'abcd'
        }
        self.test_dir = None

    def set_up_test(self, test_dir, source_files, dest_files):
        if test_dir is None:
            raise NotImplementedError('Test directory is None.')
        source = os.path.join(test_dir, 'source')
        dest = os.path.join(test_dir, 'dest')
        create_files_in_directory(source, source_files)
        create_files_in_directory(dest, dest_files)
        return source, dest
    
    def test_transfer(self):
        with tempfile.TemporaryDirectory() as test_dir:
            source, dest = self.set_up_test(test_dir, self.source_files, self.dest_files)
            transfer(source, dest)
            self.assertTrue(get_files_in_directory(dest), self.source_files.union(self.dest_files))
    
    def test_unidirectional_sync(self):
        with tempfile.TemporaryDirectory() as test_dir:
            source, dest = self.set_up_test(test_dir, self.source_files, self.dest_files)
            sync_unidirectional(source, dest)
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            self.assertEqual(get_files_in_directory(source), self.source_files)

    def test_bidirectional_sync(self):
        with tempfile.TemporaryDirectory() as test_dir:
            source, dest = self.set_up_test(test_dir, self.source_files, self.dest_files)
            sync_bidirectional(source, dest, None)
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
