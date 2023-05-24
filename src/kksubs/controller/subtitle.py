import os
from kksubs.service.sub_project import SubtitleProjectService
from typing import Dict, List
import logging
from kksubs.watcher.file_change import FileChangeWatcher

from kksubs.watcher.subtitle import SubtitleWatcher

logger = logging.getLogger(__name__)

class SubtitleController:
    def __init__(self, project_directory:str=None):
        self.project_directory = None
        self.service = None
        self.watcher = None
        if project_directory is not None:
            self.configure(project_directory=project_directory)

    def configure(self, project_directory:str):
        self.project_directory = os.path.realpath(project_directory)
        self.service = SubtitleProjectService(project_directory=self.project_directory)
        self.watcher = SubtitleWatcher(self.service)

    def info(self):
        print('Koikatsu subtitles command line tool.')

    def create(self):
        self.service.create()

    def rename(self):
        self.service.rename_images()

    def add_subtitles(
        self,
        drafts:Dict[str, List[int]]=None, prefix:str=None, 
        allow_multiprocessing:bool=None,
        allow_incremental_updating:bool=None,
        watch:bool=None,
    ):
        if watch is None:
            watch = False

        if watch:
            self.watcher.load_watch_arguments(
                drafts=drafts, prefix=prefix,
                allow_multiprocessing=allow_multiprocessing, allow_incremental_updating=allow_incremental_updating
            )
            return self.watcher.watch()

        return self.service.add_subtitles(
            drafts=drafts, prefix=prefix, 
            allow_multiprocessing=allow_multiprocessing, 
            allow_incremental_updating=allow_incremental_updating
        )

    def clear(self):
        return self.service.clear_subtitles(force=True)
    
    def close(self):
        logger.info('Closing Subtitle controller.')
        return