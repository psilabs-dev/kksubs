# TODO: test expected file operation behavior (utils/file)

# test unidirectional file sync with removing deleted files
# test unidirectional file sync without removing deleted files
# test bidirectional file sync

import os
import tempfile
import unittest

from common.utils.file import *

def create_files_in_directory(parent_directory, files:List[str]):
    if files is None or not files:
        return
    for file in files:
        dirname = os.path.join(parent_directory, os.path.dirname(file))
        file_path = os.path.join(parent_directory, file)
        os.makedirs(dirname, exist_ok=True)
        if os.path.exists(file_path) and os.path.isdir(file_path):
            continue
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
            'file1',
            'file2',
            'folder1\\file1',
            'folder1\\file2',
        }
        self.dest_files = {
            'folder2\\file3'
        }
        self.bucket_test_files = {
            'file1',
            'file2', 
            'file3', 
            'folder1\\', 
            'folder2\\', 
            'folder3\\file1',
            'folder3\\folder1\\file1',
            'folder3\\folder2\\',
        }
        self.test_dir = None

    def set_up_bucket_test(self, test_dir, bucket_test_files):
        create_files_in_directory(test_dir, bucket_test_files)
        return test_dir

    def set_up_sync_test(self, test_dir, source_files, dest_files):
        if test_dir is None:
            raise NotImplementedError('Test directory is None.')
        source = os.path.join(test_dir, 'source')
        dest = os.path.join(test_dir, 'dest')
        create_files_in_directory(source, source_files)
        create_files_in_directory(dest, dest_files)
        return source, dest
    
    def test_bucket_representation(self):
        with tempfile.TemporaryDirectory() as test_dir:
            self.set_up_bucket_test(test_dir, self.bucket_test_files)
            bucket = Bucket(path=test_dir)
            self.assertSetEqual(set(bucket.get_files().keys()), {'file1', 'file2', 'file3', 'folder3\\file1', 'folder3\\folder1\\file1'})
            self.assertSetEqual(set(bucket.get_folders().keys()), {'folder1', 'folder2', 'folder3', 'folder3\\folder1', 'folder3\\folder2'})
    
    def test_transfer(self):
        with tempfile.TemporaryDirectory() as test_dir:
            source, dest = self.set_up_sync_test(test_dir, self.source_files, self.dest_files)
            transfer(source, dest)
            self.assertTrue(get_files_in_directory(dest), self.source_files.union(self.dest_files))
    
    def test_unidirectional_sync(self):
        with tempfile.TemporaryDirectory() as test_dir:
            source, dest = self.set_up_sync_test(test_dir, self.source_files, self.dest_files)
            sync_unidirectional(source, dest)
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            self.assertEqual(get_files_in_directory(source), self.source_files)
            
            # delete folder 1, now dest should not contain folder 1.
            sf1 = os.path.join(source, 'folder1')
            df1 = os.path.join(dest, 'folder1')
            shutil.rmtree(sf1)
            sync_unidirectional(source, dest)
            self.assertFalse(os.path.exists(df1))

            # create folder 3 in source, now dest should contain folder 3.
            sf3 = os.path.join(source, 'folder3')
            df3 = os.path.join(dest, 'folder3')
            os.makedirs(sf3)
            sync_unidirectional(source, dest)
            self.assertTrue(os.path.exists(df3))

            # delete dest folder 3, dest should have foler 3 again.
            shutil.rmtree(df3)
            sync_unidirectional(source, dest)
            self.assertTrue(os.path.exists(df3))

    def test_bidirectional_sync(self):
        # logging.basicConfig(level=logging.INFO)

        with tempfile.TemporaryDirectory() as test_dir:
            source, dest = self.set_up_sync_test(test_dir, self.source_files, self.dest_files)
            synced_bucket = sync_bidirectional(source, dest, None)
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            logger.debug('Finished bsync task 1.')

            # delete folder 1 from src, now dest should not contain folder 1.
            sf1 = os.path.join(source, 'folder1')
            df1 = os.path.join(dest, 'folder1')
            shutil.rmtree(sf1)
            synced_bucket = sync_bidirectional(source, dest, synced_bucket.state())
            self.assertFalse(os.path.exists(df1))
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            self.assertEqual(get_files_in_directory(source), {
                'file1',
                'file2',
                'folder2\\file3'
            })
            logger.debug('Finished bsync task 2.')

            # add folder 3, now dest should contain folder 3.
            sf3 = os.path.join(source, 'folder3')
            df3 = os.path.join(dest, 'folder3')
            os.makedirs(sf3)
            synced_bucket = sync_bidirectional(source, dest, synced_bucket.state())
            self.assertTrue(os.path.exists(df3))
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            self.assertEqual(get_files_in_directory(source), {
                'file1',
                'file2',
                'folder2\\file3',
                # 'folder3\\',
            })
            logger.debug('Finished bsync task 3.')

            # create file in dest folder 3.
            create_files_in_directory(df3, ['file1'])
            synced_bucket = sync_bidirectional(source, dest, synced_bucket.state())
            self.assertTrue(os.path.exists(os.path.join(df3, 'file1')))
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            self.assertEqual(get_files_in_directory(source), {
                'file1',
                'file2',
                'folder2\\file3',
                'folder3\\file1',
            })
            logger.debug('Finished bsync task 4.')

            # delete folder 3 from dest, now source should not have folder 3.
            shutil.rmtree(df3)
            synced_bucket = sync_bidirectional(source, dest, synced_bucket.state())
            self.assertFalse(os.path.exists(sf3))
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            self.assertEqual(get_files_in_directory(source), {
                'file1',
                'file2',
                'folder2\\file3',
            })
            logger.debug('Finished bsync task 5.')

            # remove folder 2 from source, create folder2\\file1 in dest
            sf2 = os.path.join(source, 'folder2')
            shutil.rmtree(sf2)
            create_files_in_directory(dest, ['folder2\\file1'])
            synced_bucket = sync_bidirectional(source, dest, synced_bucket.state())
            self.assertTrue(os.path.exists(sf2))
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            self.assertEqual(get_files_in_directory(source), {
                'file1',
                'file2',
                'folder2\\file1'
            })
            logger.debug('Finished bsync task 6.')

            # remove folder 2 from dest, create folder2\\file1 in source
            df2 = os.path.join(dest, 'folder2')
            shutil.rmtree(df2)
            create_files_in_directory(source, ['folder2\\file2'])
            synced_bucket = sync_bidirectional(source, dest, synced_bucket.state())
            self.assertTrue(os.path.exists(df2))
            self.assertEqual(get_files_in_directory(source), get_files_in_directory(dest))
            self.assertEqual(get_files_in_directory(source), {
                'file1',
                'file2',
                'folder2\\file2'
            })
            logger.debug('Finished bsync task 7.')
