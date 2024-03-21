import logging
import os
import datetime

from kksubs.service.sub_project import SubtitleProjectService
from common.watcher.file_change import FileChangeWatcher

logger = logging.getLogger(__name__)

class SubtitleWatcher(FileChangeWatcher):

    def __init__(self, subtitle_project_service:SubtitleProjectService):
        super().__init__()
        self.service = subtitle_project_service

        self.watch_files([
            self.service.drafts_dir,
            self.service.images_dir,
            os.path.join(self.service.workspace_dir, 'styles.yml')
        ])

        # arguments.
        self.drafts = None
        self.prefix = None
        self.allow_multiprocessing = None
        self.allow_incremental_updating = None
        self.update_drafts = True

    def time(self):
        return datetime.datetime.now().time().strftime('%H:%M:%S')
    
    def load_watch_arguments(self, drafts=None, prefix=None, allow_multiprocessing=None, allow_incremental_updating=None):
        self.drafts = drafts
        self.prefix = prefix
        self.allow_multiprocessing = allow_multiprocessing
        self.allow_incremental_updating = allow_incremental_updating

    def event_trigger_action(self):
        formatted_time = self.time()
        logger.info(f"{formatted_time} Updates detected.")
        print(f"{formatted_time} Updates detected.")
        return self.service.add_subtitles(
            drafts=self.drafts, prefix=self.prefix,
            allow_multiprocessing=self.allow_multiprocessing,
            allow_incremental_updating=self.allow_incremental_updating,
            update_drafts=True
            )
    
    def event_idle_action(self):
        formatted_time = self.time()
        print(f"{formatted_time} No changes detected.")
        logger.info(f"{formatted_time} No changes detected.")