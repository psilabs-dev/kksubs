import os
from typing import Dict, Union
import yaml
from kksubs.data.file import Bucket

from kksubs.utils.file import transfer, sync_bidirectional, sync_unidirectional, save_most_recent_path

class FileService:

    def transfer(self, source, destination):
        return transfer(source, destination)
    
    def sync_unidirectional(self, source, destination) -> Bucket:
        return sync_unidirectional(source, destination)
    
    def sync_bidirectional(
            self, 
            source, destination, 
            previous_state:Union[str, Dict]=None,
    ) -> Union[Bucket, int]:
        
        source_exists = os.path.exists(source)
        dest_exists = os.path.exists(destination)

        if not source_exists and not dest_exists:
            return None
        if not source_exists:
            output = self.sync_unidirectional(destination, source)
            return output
        if not dest_exists:
            output = self.sync_unidirectional(source, destination)
            return output

        if os.path.isfile(source):
            output = save_most_recent_path(source, destination)

        if os.path.isdir(source):
            output = sync_bidirectional(source, destination, previous_state)
        
        return output