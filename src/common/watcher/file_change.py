import os
from typing import Dict, List
from common.watcher.abstract import AbstractWatcher

class FileChangeWatcher(AbstractWatcher):

    def __init__(self):
        super().__init__()
        self.mtsum_by_file:Dict[str, int] = dict()

    def _getmtimesum(self, file):
        if not os.path.exists(file):
            return None
        if os.path.isdir(file):
            return sum(map(os.path.getmtime, [os.path.join(file, path) for path in os.listdir(file)]))
        if os.path.isfile(file):
            return os.path.getmtime(file)

    def watch_files(self, files:List[str]):
        self.mtsum_by_file.update({file:None for file in files})

    def is_event_trigger(self) -> bool:
        # triggers if any folder or file under watch has been updated.

        change_detected = False
        for file in self.mtsum_by_file:
            prev_mtsum = self.mtsum_by_file.get(file)
            new_mtsum = self._getmtimesum(file)
            changed_file = (prev_mtsum is None and new_mtsum is not None) or (prev_mtsum is not None and new_mtsum is None) or (prev_mtsum != new_mtsum)
            change_detected = change_detected or changed_file
            self.mtsum_by_file[file] = new_mtsum

        return change_detected