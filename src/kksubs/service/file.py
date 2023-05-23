import os
from typing import Dict, List, Union
import yaml
from kksubs.data.file import Bucket

from kksubs.utils.file import transfer, sync_bidirectional, sync_unidirectional, save_most_recent_path

class FileService:

    def transfer(self, source, destination):
        return transfer(source, destination)
    
    def sync_unidirectional(self, source, destination, filename_filter:List[str]=None) -> Bucket:
        return sync_unidirectional(source, destination, filename_filter=filename_filter)
    
    def sync_bidirectional(
            self, 
            source, destination, 
            previous_state:Union[str, Dict]=None,
            last_sync_time:int=None,
    ) -> Union[Bucket, int]:
        
        source_exists = os.path.exists(source)
        dest_exists = os.path.exists(destination)

        if not source_exists and not dest_exists:
            return None
        if not source_exists:
            mtime = os.path.getmtime(destination)
            if last_sync_time is None or mtime > last_sync_time:
                output = self.sync_unidirectional(destination, source)
            else:
                output = None
            return output
        if not dest_exists:
            mtime = os.path.getmtime(source)
            if last_sync_time is None or mtime > last_sync_time:
                output = self.sync_unidirectional(source, destination)
            else:
                output = None
            return output

        if os.path.isfile(source):
            output = save_most_recent_path(source, destination)

        if os.path.isdir(source):
            output = sync_bidirectional(source, destination, previous_state)
        
        return output