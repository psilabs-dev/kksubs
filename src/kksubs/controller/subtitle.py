import os
from kksubs.service.sub_project import SubtitleProjectService
from typing import Dict, List
import logging

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

    def get_scripts_directory(self):
        # script should be more appropriate than draft.
        return self.service.drafts_dir
    
    def get_scripts(self):
        return os.listdir(self.get_scripts_directory())
    
    def get_output_directory(self):
        return self.service.get_output_directory()

    def get_output_directory_by_script(self, script_file):
        return os.path.join(self.get_output_directory(), os.path.splitext(os.path.basename(script_file))[0])

    def get_image_directory(self):
        return self.service.images_dir

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
    
    def open_output_folders(self, drafts:str=None):
        # open the folder containing subtitled images corresponding to given draft.
        # if draft is not given, opens every folder in the outputs folder.
        output_dir = self.get_output_directory()
        if drafts is not None and not drafts:
            for draft in drafts:
                draft_folder = os.path.join(output_dir, draft)
                if os.path.exists(draft_folder):
                    os.startfile(draft_folder)
                else:
                    raise FileNotFoundError(draft_folder)
                return
        
        folders = os.listdir(output_dir)
        for folder in folders:
            folder = os.path.join(output_dir, folder)
            os.startfile(folder)

    def clear(self):
        return self.service.clear_subtitles(force=True)
    
    def close(self):
        logger.info('Closing Subtitle controller.')
        return