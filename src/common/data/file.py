from enum import Enum
import os
import shutil
import time
import logging

logger = logging.getLogger(__name__)

class FileType(Enum):

    REGULAR_FILE = 1
    DIRECTORY = 2

class Bucket:
    def __init__(self, path=None, files=None, folders=None): # path must exist.

        # generate from path.
        if path is not None and not os.path.exists(path):
            raise FileNotFoundError(path)
        elif path is not None:
            self.path = path
            
            self.files = dict()
            self.folders = dict()

            for root, dirnames, filenames in os.walk(path):
                for file in filenames:
                    relative_path = os.path.join(root, file)[len(path) + 1:]
                    mtime = self.get_mtime(relative_path)
                    self.files[relative_path] = mtime

                for dir in dirnames:
                    relative_path = os.path.join(root, dir)[len(path) + 1:]
                    mtime = self.get_mtime(relative_path)
                    self.folders[relative_path] = mtime

        # generate from input
        else:
            self.path = path
            self.files = files
            self.folders = folders
        
        self.read_time = time.time()

    def get_files(self):
        return self.files
    
    def get_folders(self):
        return self.folders

    def get_file_path(self, path):
        return os.path.join(self.path, path)
    
    def get_mtime(self, filename):
        path = self.get_file_path(filename)

        if os.path.isfile(path):
            return os.path.getmtime(path)
        if os.path.isdir(path):
            max_mtime = os.path.getmtime(path)
            # for root, _, files in os.walk(path):
            #     mtimes_by_root = list(map(os.path.getmtime, map(lambda file:os.path.join(root, file), files)))
            #     if not mtimes_by_root:
            #         continue
            #     max_mtime = max([max_mtime, max(mtimes_by_root)])
            return max_mtime
        
    def get_stored_mtime(self, path, file_type):
        if file_type == FileType.REGULAR_FILE:
            return self.files[path]
        if file_type == FileType.DIRECTORY:
            return self.folders[path]

    def create_folder(self, path:str):
        path = os.path.join(self.path, path)
        os.makedirs(path, exist_ok=True)

    def is_path(self, path):
        return os.path.exists(os.path.join(self.path, path))

    def copy_to(self, other_bucket:"Bucket", path:str):
        src_path = os.path.join(self.path, path)
        if not os.path.exists(src_path):
            logger.debug(f'Error: Cannot find {path} within {self.path}')
            return
        
        target_path = os.path.join(other_bucket.path, path)
        target_directory = os.path.dirname(target_path)
        os.makedirs(target_directory, exist_ok=True)
        shutil.copy(src_path, target_path)

    def sync_most_recent(self, other_bucket:"Bucket", path:str):
        # syncs most recent file.
        path_in_a = os.path.join(self.path, path)
        path_in_b = os.path.join(other_bucket.path, path)
        if not os.path.exists(path_in_a) and not os.path.exists(path_in_b):
            logger.debug(f'Error: {path} is missing in both buckets.')
            return

        if self.files[path] > other_bucket.files[path] and self.is_path(path):
            shutil.copy(path_in_a, path_in_b)
        if self.files[path] < other_bucket.files[path] and other_bucket.is_path(path):
            shutil.copy(path_in_b, path_in_a)
        return

    def delete(self, path:str):
        # deletes path of file or folder.

        path = os.path.join(self.path, path)
        if not os.path.exists(path):
            logger.debug(f'Error: {path} is missing, cannot be deleted from bucket {self.path}.')
            return
        
        for is_type, action in [(os.path.isfile, os.remove), (os.path.isdir, shutil.rmtree)]:
            if is_type(path):
                try:
                    action(path)
                    return
                except PermissionError:
                    raise PermissionError(f'{path} cannot be deleted.')

    def state(self):
        return {
            'time': self.read_time,
            'files': self.files,
            'folders': self.folders,
        }