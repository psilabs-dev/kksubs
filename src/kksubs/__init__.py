import os
from kksubs.service.project import ProjectService
from typing import Dict, List
import logging

from kksubs.service.watcher import ProjectWatcher

logger = logging.getLogger(__name__)

def create_project(project_directory:str=None):
    print(f"Create a project here? {os.path.realpath(project_directory)}")
    confirmation = input("Enter Y to confirm: ")
    if confirmation!="Y":
        print("Operation cancelled.")
        return 1
    return ProjectService(project_directory=project_directory, create=True)

def rename_images(project_directory:str=None):
    logger.info("Renaming images.")
    return ProjectService(project_directory=project_directory).rename_images()

def add_subtitles(
        project_directory:str=None, drafts:Dict[str, List[int]]=None, prefix:str=None, 
        allow_multiprocessing:bool=None,
        allow_incremental_updating:bool=None,
        watch:bool=None,
):
    
    if watch is None:
        watch = False

    if watch:
        watcher = ProjectWatcher(ProjectService(project_directory=project_directory))
        watcher.watch(
            drafts=drafts, prefix=prefix, 
            allow_multiprocessing=allow_multiprocessing, 
            allow_incremental_updating=allow_incremental_updating
        )
        return 0

    logger.info("Adding subtitles.")
    return ProjectService(project_directory=project_directory).add_subtitles(
        drafts=drafts, prefix=prefix, 
        allow_multiprocessing=allow_multiprocessing, 
        allow_incremental_updating=allow_incremental_updating
    )

def clear_subtitles(project_directory:str=None, drafts:Dict[str, List[int]]=None, force=False):
    logger.info("Clearing subtitles.")
    return ProjectService(project_directory=project_directory).clear_subtitles(drafts=drafts, force=force)