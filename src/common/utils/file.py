from enum import Enum
import logging
import os
from os.path import getmtime
import subprocess

import shutil
from typing import Dict, List, Set

from common.data.file import Bucket

logger = logging.getLogger(__name__)

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

class FileType(Enum):

    REGULAR_FILE = 1
    DIRECTORY = 2

def sync_bidirectional_objects(
        bucket_a:Bucket, 
        bucket_b:Bucket, 
        paths_a:Set[str], 
        paths_b:Set[str], 
        paths_0:Set[str], 
        last_sync_time:int, 
        file_type:FileType
) -> Bucket:

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
    deleted_in_one_bucket = paths_a.intersection(paths_0).difference(paths_b).union(
        paths_b.intersection(paths_0).difference(paths_a)
    )
    # added to both buckets (possibly different)
    added_in_two_buckets = paths_a.intersection(paths_b).difference(paths_0)
    # added to exactly one bucket
    added_in_one_bucket = paths_a.difference(paths_b).difference(paths_0).union(
        paths_b.difference(paths_a).difference(paths_0)
    )
    # deleted from both buckets (no action needed)
    deleted = paths_0.difference(paths_a).difference(paths_b)

    total_changes = len(undeleted_modified) + len(deleted_in_one_bucket) + len(added_in_one_bucket) + len(added_in_two_buckets)
    total_num_files = total_changes + len(unmodified)
    # end of analysis
    # print(file_type, deleted_in_one_bucket, added_in_two_buckets, added_in_one_bucket, deleted)

    # start of file operations
    # apply updates.
    for path in undeleted_paths:
        if file_type == FileType.REGULAR_FILE:
            if max(bucket_a.files[path], bucket_b.files[path]) <= last_sync_time:
                continue
            bucket_a.sync_most_recent(bucket_b, path)
        if file_type == FileType.DIRECTORY:
            pass

    for path in deleted_in_one_bucket:
        # check if undeleted one is modified.
        if file_type == FileType.REGULAR_FILE:
            if path in paths_a:
                if bucket_a.files[path] > last_sync_time:
                    logger.debug(f'Copy {path} to B.')
                    bucket_a.copy_to(bucket_b, path)
                    continue
                else:
                    logger.debug(f'Delete {path} from A')
                    bucket_a.delete(path)
            if path in paths_b:
                if bucket_b.files[path] > last_sync_time:
                    logger.debug(f'Copy {path} to A.')
                    bucket_b.copy_to(bucket_a, path)
                    continue
                else:
                    logger.debug(f'Delete {path} from B.')
                    bucket_b.delete(path)
        if file_type == FileType.DIRECTORY:
            if path in paths_a:
                if bucket_a.folders[path] > last_sync_time:
                    logger.debug(f'Copy {path} to B.')
                    bucket_b.create_folder(path)
                    continue
                else:
                    logger.debug(f'Delete {path} from A')
                    bucket_a.delete(path)
            if path in paths_b:
                if bucket_b.folders[path] > last_sync_time:
                    logger.debug(f'Copy {path} to A.')
                    bucket_a.create_folder(path)
                    continue
                else:
                    logger.debug(f'Delete {path} from B.')
                    bucket_b.delete(path)
    
    for path in added_in_two_buckets:
        if file_type == FileType.REGULAR_FILE:
            logger.debug(f'Syncing {path} contents.')
            bucket_a.sync_most_recent(bucket_b, path)
        if file_type == FileType.DIRECTORY:
            pass

    for path in added_in_one_bucket:
        if file_type == FileType.REGULAR_FILE:
            if path in paths_a:
                logger.debug(f'Copy {path} to B.')
                bucket_a.copy_to(bucket_b, path)
            else:
                logger.debug(f'Copy {path} to A.')
                bucket_b.copy_to(bucket_a, path)
        if file_type == FileType.DIRECTORY:
            if path in paths_a:
                logger.debug(f'Copy {path} to B.')
                bucket_b.create_folder(path)
            else:
                logger.debug(f'Copy {path} to A.')
                bucket_a.create_folder(path)

    return

def sync_bidirectional(folder_1, folder_2, previous_state:Dict) -> Bucket:

    bucket_a = Bucket(folder_1)
    bucket_b = Bucket(folder_2)

    if previous_state is None:
        previous_state = {
            'files': [],
            'folders': [],
        }

    rfiles_a = set(bucket_a.get_files().keys())
    rfiles_b = set(bucket_b.get_files().keys())
    rfiles_0 = set(previous_state.get('files'))

    subfolders_a = set(bucket_a.get_folders().keys())
    subfolders_b = set(bucket_b.get_folders().keys())
    subfolders_0 = set(previous_state.get('folders'))

    last_sync_time = previous_state.get('time')

    sync_bidirectional_objects(bucket_a, bucket_b, subfolders_a, subfolders_b, subfolders_0, last_sync_time, FileType.DIRECTORY)
    sync_bidirectional_objects(bucket_a, bucket_b, rfiles_a, rfiles_b, rfiles_0, last_sync_time, FileType.REGULAR_FILE)

    # # for debugging
    # proceed = input('Proceed: (Y)') == 'Y'
    # if not proceed:
    #     raise KeyboardInterrupt
    # print('')

    return Bucket(folder_1)
