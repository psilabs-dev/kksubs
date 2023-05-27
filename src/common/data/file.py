import os
import shutil
import time

class Bucket:
    def __init__(self, path=None, files=None): # path must exist.

        # generate from path.
        if path is not None and not os.path.exists(path):
            raise FileNotFoundError(path)
        elif path is not None:
            self.path = path
            self.files = dict()
            for root, _, filename in os.walk(path):
                for file in filename:
                    relative_path = os.path.join(root, file)[len(path) + 1:]
                    mtime = self.get_mtime(relative_path)
                    self.files[relative_path] = mtime
        # generate from input
        else:
            self.path = path
            self.files = files
        
        self.read_time = time.time()

    def get_path(self, filename):
        return os.path.join(self.path, filename)
    
    def get_mtime(self, filename):
        return os.path.getmtime(self.get_path(filename))

    def copy_to(self, other_bucket:"Bucket", path:str):
        src_path = os.path.join(self.path, path)
        target_path = os.path.join(other_bucket.path, path)
        target_directory = os.path.dirname(target_path)
        os.makedirs(target_directory, exist_ok=True)
        shutil.copy(src_path, target_path)

    def sync_most_recent(self, other_bucket:"Bucket", path:str):
        # syncs most recent file.
        path_in_a = os.path.join(self.path, path)
        path_in_b = os.path.join(other_bucket.path, path)
        if self.files[path] > other_bucket.files[path]:
            shutil.copy(path_in_a, path_in_b)
        if self.files[path] < other_bucket.files[path]:
            shutil.copy(path_in_b, path_in_a)
        return

    def delete(self, path:str):
        path = os.path.join(self.path, path)
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                raise PermissionError(f'{path} cannot be deleted.')

    def state(self):
        return {
            'time': self.read_time,
            'files': self.files,
        }