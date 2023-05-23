import logging
import os
from os.path import getmtime

import shutil
from typing import Dict, List

from kksubs.data.file import Bucket

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

def sync_unidirectional(source, destination, filename_filter:List[str]=None):
    if filename_filter is not None:
        for target in filename_filter:
            source_target = os.path.join(source, target)
            dest_target = os.path.join(destination, target)
            sync_unidirectional(source_target, dest_target)
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
        
        source_paths = set(source_bucket.files.keys())
        dest_paths = set(dest_bucket.files.keys())
        
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

def sync_bidirectional(folder_1, folder_2, previous_state:Dict) -> Bucket:
    bucket_a = Bucket(folder_1)
    bucket_b = Bucket(folder_2)

    if previous_state is None:
        previous_state = bucket_a.state()

    last_sync_time = previous_state.get('time')

    paths_a = set(bucket_a.files.keys())
    paths_b = set(bucket_b.files.keys())
    paths_0 = set(previous_state.get('files'))

    # demorgans law
    # undeleted (but possibly modified)
    undeleted_paths = paths_a.intersection(paths_b).intersection(paths_0)
    unmodified = set(filter(lambda path: max(bucket_a.files[path], bucket_b.files[path]) <= last_sync_time, undeleted_paths))
    undeleted_modified = undeleted_paths.difference(unmodified)

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
    logger.debug(f"Found {total_num_files} files and {total_changes} changes. ({os.path.basename(folder_1)})")

    # apply updates.
    for path in undeleted_paths:
        if max(bucket_a.files[path], bucket_b.files[path]) <= last_sync_time:
            continue
        bucket_a.sync_most_recent(bucket_b, path)

    for path in deleted_in_one_bucket:
        # check if undeleted one is modified.
        if path in paths_a:
            if bucket_a.files[path] > last_sync_time:
                bucket_a.copy_to(bucket_b, path)
                continue
            else:
                os.remove(os.path.join(bucket_a.path, path))
        if path in paths_b:
            if bucket_b.files[path] > last_sync_time:
                bucket_b.copy_to(bucket_a, path)
                continue
            else:
                os.remove(os.path.join(bucket_b.path, path))
    
    for path in added_in_two_buckets:
        bucket_a.sync_most_recent(bucket_b, path)

    for path in added_in_one_bucket:
        if path in paths_a:
            bucket_a.copy_to(bucket_b, path)
        else:
            bucket_b.copy_to(bucket_a, path)

    return Bucket(folder_1)