import logging
import os
from os.path import getmtime
import subprocess

import shutil
import time
from typing import Dict, List, Set

from common.data.file import Bucket, FileType
from common.data.representable import RepresentableData
from common.utils.coalesce import coalesce

logger = logging.getLogger(__name__)


    # total_changes = len(undeleted_modified) + len(deleted_in_one_bucket) + len(added_in_one_bucket) + len(added_in_two_buckets)
    # total_num_files = total_changes + len(unmodified)

def get_parents(path):
    parents = set()
    dirname = os.path.dirname(path)
    dirs = dirname.split(os.sep)
    for i in range(1, len(dirs)+1):
        parents.add(os.sep.join(dirs[:i]))
    return parents

class SyncDeltas(RepresentableData):

    def __init__(
            self,
            unmodified:Set[str]=None,
            undeleted_modified:Set[str]=None,
            delete_from_a:Set[str]=None,
            delete_from_b:Set[str]=None,
            add_to_a:Set[str]=None,
            add_to_b:Set[str]=None,
            add_to_both:Set[str]=None,
    ):
        self.unmodified = unmodified
        self.undeleted_modified = undeleted_modified
        self.delete_from_a = delete_from_a
        self.delete_from_b = delete_from_b
        self.add_to_a = add_to_a
        self.add_to_b = add_to_b
        self.add_two = add_to_both

    def deserialize(self, sync_deltas_data):
        return SyncDeltas(**sync_deltas_data)

class SyncDeltaService:

    def __init__(self, file_deltas:SyncDeltas, folder_deltas:SyncDeltas, bucket_a:Bucket, bucket_b:Bucket, last_sync_time:int):
        self.file_deltas = file_deltas
        self.folder_deltas = folder_deltas
        self.bucket_a = bucket_a
        self.bucket_b = bucket_b
        self.last_sync_time = last_sync_time

    def action_unmodified(self, file_path:str, file_type:FileType):
        pass

    def action_undeleted_modified(self, file_path:str, file_type:FileType):
        if file_type == FileType.REGULAR_FILE:
            self.bucket_a.sync_most_recent(self.bucket_b, file_path)
            logger.debug(f'synced {file_path}')
        if file_type == FileType.DIRECTORY:
            pass

    def action_delete_from_a(self, file_path:str, file_type:FileType):
        if self.bucket_b.get_stored_mtime(file_path, file_type) > self.last_sync_time:
            if file_type == FileType.REGULAR_FILE:
                self.bucket_b.copy_to(self.bucket_a, file_path)
                logger.debug(f'Copied {file_path} to A (override delete in A)')
            if file_type == FileType.DIRECTORY:
                self.bucket_a.create_folder(file_path)
                logger.debug(f'Created folder {file_path} (override delete in A)')
        else:
            self.bucket_b.delete(file_path)
            logger.debug(f'Deleted {file_path} from B.')

    def action_delete_from_b(self, file_path:str, file_type:FileType):
        if self.bucket_a.get_stored_mtime(file_path, file_type) > self.last_sync_time:
            if file_type == FileType.REGULAR_FILE:
                self.bucket_a.copy_to(self.bucket_b, file_path)
                logger.debug(f'Copied {file_path} to B. (override delete in B)')
            if file_type == FileType.DIRECTORY:
                self.bucket_b.create_folder(file_path)
                logger.debug(f'Created {file_path} in B. (override delete in B)')
        else:
            self.bucket_a.delete(file_path)
            logger.debug(f'Deleted {file_path} from A.')

    def action_add_to_a(self, file_path:str, file_type:FileType):
        if file_type == FileType.REGULAR_FILE:
            self.bucket_a.copy_to(self.bucket_b, file_path)
            logger.debug(f'Copied {file_path} to B.')
        else:
            self.bucket_b.create_folder(file_path)
            logger.debug(f'Created {file_path} in B.')

    def action_add_to_b(self, file_path:str, file_type:FileType):
        if file_type == FileType.REGULAR_FILE:
            self.bucket_b.copy_to(self.bucket_a, file_path)
            logger.debug(f'Copied {file_path} to A.')
        else:
            self.bucket_a.create_folder(file_path)
            logger.debug(f'Created {file_path} in A.')

    def action_add_two(self, file_path:str, file_type:FileType):
        if file_type == FileType.REGULAR_FILE:
            self.bucket_a.sync_most_recent(self.bucket_b, file_path)
            logger.debug(f'Synced {file_path} contents.')
        if file_type == FileType.DIRECTORY:
            pass

    def resolve_folder_file_delta_conflicts(self):
        # if add folder/file to A after folder deleted in B, file takes priority
        add_to_a = self.file_deltas.add_to_a
        keep_in_b = set()
        for path in add_to_a:
            keep_in_b = keep_in_b.union(get_parents(path))
        self.folder_deltas.delete_from_b = self.folder_deltas.delete_from_b.difference(keep_in_b)
        self.folder_deltas.add_to_a = self.folder_deltas.add_to_a.union(keep_in_b)
        logger.debug(f'Moved {keep_in_b} from delete_from_b to add_to_a.')

        add_to_b = self.file_deltas.add_to_b
        keep_in_a = set()
        for path in add_to_b:
            keep_in_a = keep_in_a.union(get_parents(path))
        self.folder_deltas.delete_from_a = self.folder_deltas.delete_from_a.difference(keep_in_a)
        self.folder_deltas.add_to_b = self.folder_deltas.add_to_b.union(keep_in_a)
        logger.debug(f'Moved {keep_in_a} from delete_from_a to add_to_b.')

        # TODO: if a folder is being deleted anyways, files that are to be deleted should be removed.

    def apply_deltas(self):
        for deltas_by_type, file_type in [(self.folder_deltas, FileType.DIRECTORY), (self.file_deltas, FileType.REGULAR_FILE)]:
            for paths, action in [
                (deltas_by_type.unmodified, self.action_unmodified),
                (deltas_by_type.undeleted_modified, self.action_undeleted_modified),
                (deltas_by_type.delete_from_a, self.action_delete_from_a),
                (deltas_by_type.delete_from_b, self.action_delete_from_b),
                (deltas_by_type.add_to_a, self.action_add_to_a),
                (deltas_by_type.add_to_b, self.action_add_to_b),
                (deltas_by_type.add_two, self.action_add_two),
            ]:
                for path in paths:
                    action(path, file_type)
        logger.debug('Deltas applied.')

def save_most_recent_path(path_1, path_2) -> int:
    output = max(getmtime(path_1), getmtime(path_2))
    time_1, time_2 = getmtime(path_1), getmtime(path_2)
    
    if time_1 != time_2:
        if time_1 > time_2:
            source, dest = path_1, path_2
        else:
            source, dest = path_2, path_1
        shutil.copy2(source, dest)
        logger.info(f'Found change at {source}.')

    return output

# intended use: copy UserData/cap to workspace/images.
def transfer(source:str, destination:str):
    if not os.path.exists(source):
        return
    if os.path.isfile(source):
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(source, destination)
    elif os.path.isdir(source):
        if not os.path.exists(destination):
            return
        shutil.copytree(source, destination, copy_function=shutil.copy2, dirs_exist_ok=True)
        return

# old version of unidirectional sync.
def _sync_unidirectional(source, destination, filename_filter:List[str]=None):
    if filename_filter is not None:
        for target in filename_filter:
            source_target = os.path.join(source, target)
            dest_target = os.path.join(destination, target)
            _sync_unidirectional(source_target, dest_target)
        return Bucket(path=source)

    # assumption that destination does not get changed.
    if not os.path.exists(source):
        return
    if os.path.isfile(source):
        source_bucket = Bucket(path=source)
        transfer(source, destination)
    elif os.path.isdir(source):
        os.makedirs(destination, exist_ok=True)
        source_bucket = Bucket(path=source)
        dest_bucket = Bucket(path=destination)
        
        source_paths = set(source_bucket.get_files().keys())
        dest_paths = set(dest_bucket.get_files().keys())
        
        in_both = source_paths.intersection(dest_paths) # conflict resolution. (see modified/unmodified)
        modified = set(filter(lambda path: source_bucket.files[path] > dest_bucket.files[path], in_both))
        unmodified = in_both.difference(modified)
        delete_from_dest = dest_paths.difference(source_paths)
        add_to_dest = source_paths.difference(dest_paths)

        for path in modified.union(add_to_dest):
            source_bucket.copy_to(dest_bucket, path)
            continue
        for path in delete_from_dest:
            try:
                dest_bucket.delete(path)
            except:
                print(path)
                raise
        # for path in unmodified:
        #     continue
    return source_bucket

def sync_unidirectional(source, destination, filename_filter:List[str]=None, enable_log=False):
    if filename_filter is not None:
        for target in filename_filter:
            source_target = os.path.join(source, target)
            dest_target = os.path.join(destination, target)
            sync_unidirectional(source_target, dest_target, enable_log=enable_log)

    # run robocopy without outputting stuff.
    command = ['robocopy', source, destination, '/MIR']
    if enable_log:
        subprocess.run(command)
    else:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _get_bidirectional_deltas(
        bucket_a:Bucket, 
        bucket_b:Bucket, 
        paths_a:Set[str], 
        paths_b:Set[str], 
        paths_0:Set[str], 
        last_sync_time:int, 
        file_type:FileType
) -> SyncDeltas:
    # start of analysis
    # undeleted (but possibly modified)
    undeleted_paths = paths_a.intersection(paths_b).intersection(paths_0)
    if file_type == FileType.REGULAR_FILE:
        unmodified = set(filter(lambda path: max(bucket_a.files[path], bucket_b.files[path]) <= last_sync_time, undeleted_paths))
        undeleted_modified = undeleted_paths.difference(unmodified)

    elif file_type == FileType.DIRECTORY:
        unmodified = undeleted_paths
        undeleted_modified = set()

    # deleted from exactly one bucket (undeleted one is possibly modified)
    delete_from_a = paths_b.intersection(paths_0).difference(paths_a)
    delete_from_b = paths_a.intersection(paths_0).difference(paths_b)

    # added to both buckets (possibly different)
    added_in_two_buckets = paths_a.intersection(paths_b).difference(paths_0)

    # added to exactly one bucket
    add_to_a = paths_a.difference(paths_b).difference(paths_0)
    add_to_b = paths_b.difference(paths_a).difference(paths_0)

    # deleted from both buckets (no action needed)
    deleted = paths_0.difference(paths_a).difference(paths_b)

    total_changes = sum(map(len, [
        undeleted_modified,
        delete_from_a,
        delete_from_b,
        add_to_a,
        add_to_b,
        added_in_two_buckets,
        deleted,
    ]))

    total_num_files = total_changes + len(unmodified)

    return SyncDeltas(
        unmodified=unmodified,
        undeleted_modified=undeleted_modified,
        delete_from_a=delete_from_a,
        delete_from_b=delete_from_b,
        add_to_a=add_to_a,
        add_to_b=add_to_b,
        add_to_both=added_in_two_buckets,
    )

def sync_bidirectional(folder_1, folder_2, previous_state:Dict) -> Bucket:
    bucket_a = Bucket(folder_1)
    bucket_b = Bucket(folder_2)

    if previous_state is None:
        previous_state = {
            'files': dict(),
            'folders': dict(),
        }

    rfiles_a = set(bucket_a.get_files().keys())
    rfiles_b = set(bucket_b.get_files().keys())
    rfiles_0 = set(coalesce(previous_state.get('files'), set()))

    subfolders_a = set(bucket_a.get_folders().keys())
    subfolders_b = set(bucket_b.get_folders().keys())
    subfolders_0 = set(coalesce(previous_state.get('folders'), set()))

    last_sync_time = previous_state.get('time')

    folder_deltas = _get_bidirectional_deltas(bucket_a, bucket_b, subfolders_a, subfolders_b, subfolders_0, last_sync_time, FileType.DIRECTORY)
    file_deltas = _get_bidirectional_deltas(bucket_a, bucket_b, rfiles_a, rfiles_b, rfiles_0, last_sync_time, FileType.REGULAR_FILE)
    logger.info(f'Obtained folder deltas: {folder_deltas}')
    logger.info(f'Obtained file deltas:   {file_deltas}')

    # check certain things
    # if a folder is deleted in X but a file is added in Y/folder, then the folder cannot be deleted.

    deltas_service = SyncDeltaService(file_deltas, folder_deltas, bucket_a, bucket_b, last_sync_time)
    deltas_service.resolve_folder_file_delta_conflicts()

    deltas_service.apply_deltas()
    logger.debug('Concluded bidirectional sync.')

    # sleep to stabilize newly created file mtimes with new sync time.
    time.sleep(0.1)

    return Bucket(folder_1)
